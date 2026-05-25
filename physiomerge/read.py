"""
read.py
=======
Batch-load physiological data files

The "READ" command is used for reading for reading structured data from various file formats (LabChart, ADI, Terason, Respirac). It supports multi-channel data, variable sampling frequencies, and annotation extraction.

Imports:
--------
- `adi` for reading ADI LabChart files

Example:
--------
An example of a Read command configuration:

.. code-block:: toml

    [[command]]
    class_name = "read"
    folder = "datasets/shch/labchart/"
    file = ["SHCH_106_V1"]
    ext = ".adicht"
    format = "ADI"
    verbosity = "debug"

Explanation of keys:
--------
- **folder**: The folder where the files are located.
- **file**: The filename or list of filenames to read.
- **ext**: The file extension (e.g., ".adicht").
- **format**: The file format type. Supported values: `"LABCHART"`, `"ADI"`, `"TERASON"`, `"RESPIRAC"`.
- **verbosity**: Optional logging verbosity level.
"""

import numpy as np
import adi
from pathlib import Path
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from scipy import interpolate
import pandas as pd
from itertools import repeat

from common import Command


class Read(Command):
    """
    Command class to read data files into structured variable dictionaries.

    Attributes
    ----------
    folder : str or list
        Folder path(s) where files are located.
    filename : str or list
        Name(s) of file(s) to read.
    extension : str or list
        File extension(s) to read.
    format : str or list
        File format(s) for reading. Must be one of 'LABCHART', 'ADI', 'TERASON', 'RESPIRAC'.
    good : bool
        Indicates if the instance passed validation.
    """

    def __init__(self, command: dict) -> None:
        """
        Initializes the Read command with a dictionary of parameters.

        Parameters
        ----------
        command : dict
            Dictionary containing configuration keys such as folder, file, ext, and format.
        """
        super().__init__(command)
        self.folder = command.get("folder", "")
        self.filename = command.get("file", "")
        self.extension = command.get("ext", "")
        self.format = command.get("format", "")

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validates the Read instance to ensure it meets the required criteria.

        Checks include:
        - Type checks for string or list attributes
        - Ensuring all lists have matching lengths
        - Format validation
        - Base class validation

        Returns
        -------
        bool
            True if the instance is valid, False otherwise.
        """
        is_valid = True

        required_attributes = ["folder", "filename", "extension", "format"]
        for attr_name in required_attributes:
            value = getattr(self, attr_name)
            if not isinstance(value, (str, list)):
                self.print(
                    "error",
                    f"'{attr_name}' must be a string or list, but got {type(value).__name__}.",
                )
                is_valid = False

        try:
            self.equal_size(["folder", "filename", "extension", "format"])
        except ValueError as e:
            self.print("error", f"Validation failed: {e}")
            is_valid = False

        self.string_upper(["format"])
        if not self.is_in_array(
            self.format,
            [
                "LABCHART",
                "ADI",
                "TERASON",
                "RESPIRAC",
            ],
        ):
            is_valid = False

        if not super().validate() or not is_valid:
            self.print("error", f"{self.type} class is not valid")
            return False

        self.print("debug", f"{self.type} class is valid")
        return True

    def execute(
        self, variables: dict[str, list[dict[str, any]]]
    ) -> dict[str, list[dict[str, any]]]:
        """
        Executes the Read command, reading files and returning structured variable data.

        Parameters
        ----------
        variables : dict
            Dictionary where keys are variable names and values are lists of dictionaries.

        Returns
        -------
        dict
            Updated dictionary with the read data stored under `self.resultant`.
        """
        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        people = []

        for folder, filename, extension, format in zip(
            self.folder, self.filename, self.extension, self.format
        ):
            reading_filename = folder + filename + extension
            person = None
            if format == "LABCHART":
                person = self.read_labchart(reading_filename, filename)
            if format == "ADI":
                person = self.read_labchart_adi(reading_filename, filename)
            elif format == "TERASON":
                person = self.read_terason(reading_filename, filename)
            elif format == "RESPIRAC":
                person = self.read_respirac(reading_filename, filename)
            if person:
                person["COLUMNS"] = [col.upper() for col in person["COLUMNS"]]
                people.append(person)

        variables[self.resultant] = people
        return variables

    def read_labchart_adi(self, filepath: str, filename: str) -> dict[str, any]:
        """
        Reads a LabChart .adicht file using the ADI API.

        Pads shorter channels at the start. COMMENTS is a list of strings,
        MARKERS a list of lists, aligned per sample.

        Parameters
        ----------
        filepath : str
            Full path to the ADI file.
        filename : str
            Base name of the file.

        Returns
        -------
        dict
            Dictionary containing DATA, COLUMNS, COMMENTS, MARKERS, FREQUENCY, FILENAME.
        """
        self.print("debug", f"Reading LabChart file with ADI: {filepath}")
        try:
            f = adi.read_file(filepath)
        except Exception as e:
            self.print("error", f"Failed to open file '{filepath}': {e}")
            return {}

        # --- Combine all channels into a 2D array ---
        all_channels = []
        channel_lengths = []
        col_names = []

        # First get the maximum sampling frequency
        max_fs = 200
        for ch in f.channels:
            ch_max_fs = max(ch.fs)
            max_fs = max(ch_max_fs, max_fs)

        for ch in f.channels:
            ch_data = []
            for rec_id in range(1, ch.n_records + 1):
                rec_fs = ch.fs[rec_id - 1]
                try:
                    rec_data = ch.get_data(rec_id)
                    if len(rec_data) == 0:
                        rec_data = np.zeros(1)
                except ValueError:
                    rec_data = np.zeros(1)

                # Not all records are at the same sampling frequency
                # upsample to higher frequency
                if rec_fs != max_fs:
                    x_original = np.linspace(0, rec_data.shape[0])
                    old_len = rec_data.shape[0]
                    new_len = int(old_len * max_fs / rec_fs)

                    x_original = np.arange(old_len)
                    x_new = np.linspace(0, old_len, new_len)

                    interp_func = interpolate.interp1d(
                        x_original,
                        rec_data,
                        kind="previous",
                        bounds_error=False,
                        fill_value=(rec_data[0], rec_data[-1]),
                    )

                    rec_data = interp_func(x_new)

                ch_data.append(rec_data)
            ch_data = np.concatenate(ch_data)
            all_channels.append(ch_data)
            channel_lengths.append(len(ch_data))
            col_names.append(ch.name)
        # Fix col names
        col_names = [name.replace(' ', '_') for name in col_names]
        
        fs = max_fs

        # --- Determine maximum length and start-pad shorter channels ---
        max_len = max(channel_lengths)
        for i in range(len(all_channels)):
            if len(all_channels[i]) < max_len:
                pad_width = max_len - len(all_channels[i])
                all_channels[i] = np.pad(all_channels[i], (pad_width, 0))

        data_array = np.column_stack(all_channels)

        # --- Create COMMENTS and MARKERS lists ---
        comments_list = [""] * max_len
        markers_list = [[] for _ in range(max_len)]

        # Keep track of cumulative start index per record
        rec_cumulative_start = 0
        for rec in f.records:
            comments_list[rec_cumulative_start] = "RESET"
            for c in rec.comments:
                continuous_sample = rec_cumulative_start + c.tick_position
                if continuous_sample < max_len:
                    comments_list[continuous_sample] = c.text.strip()
                    markers_list[continuous_sample] = [c.id]
            rec_cumulative_start += rec.n_ticks

        # --- TIME column ---
        time_vector = np.arange(max_len) / fs
        col_names = ["TIME"] + col_names
        data_array = np.column_stack([time_vector, data_array])

        self.print(
            "index",
            f"{filepath}: array size {data_array.shape} containing {len([c for c in comments_list if c])} comments",
        )

        return {
            "DATA": data_array,
            "COLUMNS": col_names,
            "COMMENTS": comments_list,
            "MARKERS": markers_list,
            "FREQUENCY": fs,
            "FILENAME": filename,
        }

    def read_labchart(self, filepath: str, filename: str) -> dict[str, any]:
        """
        Reads a LabChart text file.

        Parameters
        ----------
        filepath : str
            Full path to the LabChart text file.
        filename : str
            Base name of the file.

        Returns
        -------
        dict
            Dictionary containing DATA, COLUMNS, COMMENTS, MARKERS, FREQUENCY, FILENAME.
        """
        self.print("debug", f"Reading Labchart file: {filepath}")

        if not Path(filepath).is_file():
            self.print("error", f"File not found: '{filepath}', skipping.")
            return {}

        fs = 200  # If it cant find the "interval", assume 200?
        data_rows = []
        comments = []
        markers = []
        col_names = []

        reset = True
        marker_pattern = re.compile(
            r"#(\d+)\s+Event Marker"
        )  # Matches markers like #20 Event Marker
        comment_pattern = re.compile(r"#\*\s*(.+)")  # Matches comments like #* XXXX

        with open(filepath, "r") as fp:
            for line in fp:
                line = line.strip()

                # Header Code
                # Sampling Frequency Data
                if line.startswith("Interval="):
                    try:
                        period = float(line.split("\t")[1].replace(" s", ""))
                        fs_ = 1 / period
                        if len(data_rows) == 0:
                            fs = fs_
                        elif fs_ != fs:
                            self.print("error", "Sampling frequency mismatch")
                            return None
                    except (ValueError, IndexError):
                        self.print("error", f"Malformed Interval line: {line}")
                        return {}

                # Channel Names
                if line.startswith("ChannelTitle="):
                    headers = line.split("\t")
                    headers = [
                        header for header in headers if header != "ChannelTitle="
                    ]
                    col_names = ["TIME"] + [
                        header.replace(" ", "").strip("(){}").upper()
                        for header in headers
                    ]

                if not line[0].isdigit():
                    reset = True

                # Non Header Code
                if line[0].isdigit():
                    row = []
                    marks = []
                    comms = ""

                    data_parts = line.split("\t")
                    for part in data_parts:
                        # Checking if the data is a comment
                        if part.startswith("#"):
                            comment_match = comment_pattern.findall(part)
                            marker_matches = marker_pattern.findall(part)

                            if comment_match:
                                for comment in comment_match:
                                    comment_text = (
                                        comment.replace(" ", "").strip("(){}").upper()
                                    )
                                self.print(
                                    "index",
                                    f"Recorded a comment with the index '{comment_text}'",
                                )
                                comms = comment_text

                            if marker_matches:
                                for match in marker_matches:
                                    marks.append(int(match))
                        else:
                            try:
                                row.append(float(part))
                            except ValueError:
                                # self.print("index", f"encountered non-float text, replacing with 0 : '{part}'")
                                row.append(0)

                    # Everytime a new header shows up we consider it a reset
                    if reset:
                        reset = False
                        comms = "RESET"

                    # Append line number
                    data_rows.append(row)
                    comments.append(comms)
                    markers.append(marks)

        # Find the maximum size of the rows
        max_size = max(len(row) for row in data_rows)

        # Make all rows the same size by padding with zeros
        for i, row in enumerate(data_rows):
            if len(row) < max_size:
                # Pad the row with zeros
                data_rows[i] = row + [0] * (max_size - len(row))

        data_array = np.array(data_rows)

        self.print(
            "index",
            f"{filepath}: array size {data_array.shape} containing {len(comments)} comments",
        )
        person = {
            "DATA": data_array,
            "COLUMNS": col_names,
            "COMMENTS": comments,
            "MARKERS": markers,
            "FREQUENCY": fs,
            "FILENAME": filename,
        }
        return person

    def read_terason(self, filepath: str, filename: str) -> dict[str, any]:
        """
        Reads a Terason formatted file.

        Parameters
        ----------
        filepath : str
            Full path to the Terason file.
        filename : str
            Base name of the file.

        Returns
        -------
        dict
            Dictionary containing DATA, COLUMNS, COMMENTS, MARKERS, FREQUENCY, FILENAME.
        """

        self.print("debug", f"Reading Terason file: {filepath}")

        if not Path(filepath).is_file():
            self.print("error", f"File not found: '{filepath}', skipping.")
            return {}

        fs = -1  # Currently all readings from terason are 200 Hz.
        data_rows = []
        comments = []
        markers = []
        col_names = []
        data_started = False
        header_info = {}  # Store header metadata

        with open(filepath, "r") as fp:
            for line in fp:
                line = line.strip()
                
                # Look for the {Data} marker to start data reading
                if line.startswith("{Data}"):
                    data_started = True
                    continue

                # Parse header information (lines with curly braces or key-value pairs)
                if not data_started:
                    parts = line.split(",")
                    if len(parts) >= 2:
                        key = parts[0].strip("{} ")
                        value = parts[1].strip()
                        header_info[key] = value
                
                if data_started:
                    if not line:
                        continue
                    
                    # Handle column headers (the line before data starts)
                    if not line[0].isdigit() and col_names == []:
                        line = line.replace("(sec)", "").replace("(cm)", "").replace("(cm/s)", "")
                        line = line.replace("(", "").replace(")", "").replace(" ", "")
                        col_names = line.split(",")
                        self.print("index", f"Column names :{col_names}")
                        continue

                if data_started and line[0].isdigit():
                    row = []
                    marks = []

                    data_parts = line.split(",")
                    okay = True
                    for part, name in zip(data_parts, col_names):
                        if name == "Time":
                            if fs == -1:
                                pass
                                #if float(part) != 0.0:
                                #fs = 182# REMINDER TO REMOVE (ONLY KEEP FOR TCBF)
                                #fs = 1/float(part) # ORIGINAL
                        if name == "R-wave":
                            if round(float(part)) == 1:
                                marks.append(1)
                                marks.append(2)
                        if name == "DeletedData":
                            if float(part) != 0.0:
                                okay = False

                        row.append(float(part))
                    if okay:
                        data_rows.append(row)
                    else:
                        if data_rows:
                            self.print(
                                "index",
                                f"deleted some bad data {row}, instead using {data_rows[-1]}",
                            )
                            data_rows.append(data_rows[-1])
                        else:
                            self.print(
                                "index",
                                f"deleted some bad data {row}, instead using {[0] * len(row)}",
                            )
                            data_rows.append([0] * len(row))
                    markers.append(marks)

        start_parts = header_info["Start Time (hh:mm:ss)"].split(":")
        end_parts = header_info["End Time (hh:mm:ss)"].split(":")
        if len(start_parts) == 3 and len(end_parts) == 3:
            start_seconds = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + int(start_parts[2])
            end_seconds = int(end_parts[0]) * 3600 + int(end_parts[1]) * 60 + int(end_parts[2])
            
            total_duration = end_seconds - start_seconds
            fs = round(len(data_rows) / total_duration)
            self.print("debug", f"Calculated sampling frequency from duration: {fs} Hz")

        # Find the maximum size of the rows
        max_size = max(len(row) for row in data_rows)

        # Make all rows the same size by padding with zeros
        for i, row in enumerate(data_rows):
            if len(row) < max_size:
                # Pad the row with zeros
                data_rows[i] = row + [0] * (max_size - len(row))

        data_array = np.array(data_rows)

        self.print(
            "debug",
            f"{filepath}: array size {data_array.shape} containing {len(comments)} comments",
        )
        person = {
            "DATA": data_array,
            "COLUMNS": col_names,
            "COMMENTS": comments,
            "MARKERS": markers,
            "FREQUENCY": fs,
            "FILENAME": filename,
        }

        return person

    def read_respirac(self, filepath: str, filename: str) -> dict[str, any]:
        """
        Reads a Respirac CSV file.

        Parameters
        ----------
        filepath : str
            Full path to the CSV file.
        filename : str
            Base name of the file.

        Returns
        -------
        dict
            Dictionary containing DATA, COLUMNS, COMMENTS, MARKERS, FREQUENCY, FILENAME.
        """
        self.print("debug", f"Reading Respirac file: {filepath}")

        df = pd.read_csv(filepath)
        fs = 1000  # default for respirac

        #df["respiratory_length"] = df["MR Time(s)"] - (df["Start Inspire (sec)"] / 1000)
        df["MR Time(s)"] = pd.to_numeric(df["MR Time(s)"], errors='coerce')
        time_diffs = df["MR Time(s)"].diff().shift(-1)  # Next row minus current row
        if len(time_diffs) > 1:
            avg_diff = time_diffs.iloc[:-1].mean()
            time_diffs.iloc[-1] = avg_diff if not pd.isna(avg_diff) else 1.0*fs
        else:
            time_diffs.iloc[0] = 1.0*fs
        
        df["respiratory_length"] = time_diffs*fs


        column_mapping = {
            
            "Desired PO2 (mmHg)": "desired_po2",
            "Desired PCO2 (mmHg)": "desired_pco2",
            "Achievable PO2 (mmHg)": "achievable_po2",
            "Achievable PCO2 (mmHg)": "achievable_pco2",
            "PO2 (mmHg)": "po2",
            "PCO2 (mmHg)": "pco2",
            "Resting PO2 (mmHg)": "resting_po2",
            "Resting PCO2 (mmHg)": "resting_pco2",
            "PBaro (mmHg)": "pbaro",
            #"Inspire time (seconds)": "inspire_time",
            #"Expire time (seconds)": "expire_time",
            "Breath idx": "breath_idx",
            "Tidal volume (mL)": "tidal_volume",
            "Respiration rate (BPM)": "respiration_rate",
            #"Start Inspire (sec)": "start_inspire",
            "O2 Adjustment (mmHg)": "o2_adjustment",
            "CO2 Adjustment (mmHg)": "co2_adjustment",
            "G1 Target vol (mL)": "g1_target_vol",
            "G1 FCO2 (%)": "g1_fco2",
            "G1 FO2 (%)": "g1_fo2",
            "G2 FCO2 (%)": "g2_fco2",
            "G2 FO2 (%)": "g2_fo2",
            #"Sig": "sig"
        }
        df = df.rename(columns=column_mapping)
    
        # Keep only the renamed columns plus respiratory_length
        selected_columns = list(column_mapping.values()) + ["respiratory_length"]
        df = df[selected_columns]

        # Convert all selected columns to numeric, coercing errors to NaN
        for col in selected_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        
        col_names = list(df.columns)



        data_rows = []
        comments = []
        markers = []
        # Now you can process all columns
        for index, row in df.iterrows():
            length = int(row["respiratory_length"])
            
            # Extract ALL columns in the order they appear in the DataFrame
            data = [row[col] for col in col_names]
            data_rows.extend([data.copy() for _ in range(length)])

            marks = []
            markers.extend([[] for _ in range(length)])
            markers[-1] = [i for i in range(len(col_names))]
        data_array = np.array(data_rows)



        person = {
            "DATA": data_array,
            "COLUMNS": col_names,
            "COMMENTS": comments,
            "MARKERS": markers,
            "FREQUENCY": fs,
            "FILENAME": filename,
        }
        return person

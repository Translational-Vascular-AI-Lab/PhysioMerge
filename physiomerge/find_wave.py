from scipy.signal import find_peaks

from common import Command, copy_dict, time_from_string, find_indices


class FindWave(Command):
    """
    FindWave Command - Peak detection in time-series data.

    Detects peaks (maxima) or valleys (minima) in continuous data channels using
    the scipy.signal.find_peaks algorithm. Identified features are marked in the
    data for subsequent processing steps.

    Attributes
    ----------
    difference : str
        Minimum time difference between detected peaks, specified as a time string
        (e.g., "10s", "500ms") or number of samples.
    prominence : int or float
        Minimum prominence of peaks. The prominence of a peak measures how much
        a peak stands out from the surrounding baseline.
    height : int or float
        Minimum height of peaks. Peaks below this threshold are ignored.
        If 0, height constraint is not applied.
    format : str
        Detection mode: "MAX" for detecting peaks (maxima) or "MIN" for detecting
        valleys (minima).
    good : bool
        Validation status indicating whether the command is properly configured.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize a FindWave command instance.

        Parameters
        ----------
        command : dict
            Configuration dictionary containing:

            - "difference" : str
                Minimum time/sample difference between detected peaks
            - "prominence" : int or float
                Minimum prominence of peaks
            - "height" : int or float
                Minimum height of peaks (0 to disable)
            - "format" : str
                Detection mode: "MAX" or "MIN"
            - Additional parameters inherited from Command base class:
              "name", "resultant", "channel"
        """
        super().__init__(command)
        self.difference = command.get("difference", "")
        self.prominence = command.get("prominence", 0)
        self.height = command.get("height", 0)
        self.format = command.get("format", "MAX")
        self.overwrite = command.get("overwrite", True)

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validate the FindWave instance configuration.

        Performs comprehensive validation including type checking, parameter
        validation, size consistency checks, and base class validation.

        Returns
        -------
        bool
            True if the instance is valid, False otherwise.

        Notes
        -----
        Validation includes:
        1. Type checking for numeric and string parameters
        2. Format validation (must be "MAX" or "MIN")
        3. Size consistency across parameter lists
        4. Base class validation
        """
        is_valid = True

        required_int = ["prominence", "height"]
        if not self.check_type_inner(required_int, [int, float]):
            is_valid = False

        required_str = ["difference"]
        if not self.check_type_inner(required_str, [str]):
            is_valid = False

        required_bool = ["overwrite"]
        if not self.check_type_inner(required_bool, [bool]):
            is_valid = False

        try:
            self.equal_size(
                [
                    "name",
                    "resultant",
                    "channel",
                    "difference",
                    "prominence",
                    "height",
                    "format",
                    "overwrite",
                ]
            )
        except ValueError as e:
            self.print("error", f"Validation failed: {e}")
            is_valid = False

        if is_valid:
            self.string_upper(["format"])

        valid_formats = ["MAX", "MIN"]
        if not self.is_in_array(self.format, valid_formats):
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
        Execute the FindWave command on the provided variables.

        Parameters
        ----------
        variables : dict[str, list[dict[str, any]]]
            Dictionary containing input data variables keyed by variable name.
            Each value is a list of person dictionaries containing:
            - "FILENAME": Unique identifier for the person/recording
            - "DATA": 2D numpy array of time-series data
            - "COLUMNS": List of column names corresponding to DATA
            - "MARKERS": List of marker lists for each sample
            - "FREQUENCY": Sampling frequency in Hz

        Returns
        -------
        dict[str, list[dict[str, any]]]
            Dictionary with peak/valley markers added to the output variables.
            Detected features are marked in the MARKERS list for each person.

        Notes
        -----
        - If the command is invalid (self.good is False), returns input unchanged
        - Existing markers for the channel are cleared before adding new ones
        - The difference parameter is converted from time string to samples
        - Empty results are handled gracefully
        """
        if not self.good:
            self.print("error", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")

        for name, resultant, channel, difference, prominence, height, format, overwrite in zip(
            self.name,
            self.resultant,
            self.channel,
            self.difference,
            self.prominence,
            self.height,
            self.format,
            self.overwrite,
        ):
            new_people = []
            if name not in variables:
                self.print(
                    "error", f"the variable name {name} is not in {variables.keys()}"
                )
            if variables.get(name) == []:
                self.print("warning", f"{name} is currently a empty list")
            for person_ in variables.get(name):
                person = copy_dict(person_)
                person = self.find_wave(
                    person, channel, difference, prominence, height, format, overwrite
                )
                new_people.append(person)
            variables[resultant] = new_people

        return variables

    def find_wave(self, person, channel, difference, prominence, height, format, overwrite):
        """
        Detect peaks or valleys in a single person's data channel.

        Parameters
        ----------
        person : dict[str, any]
            Dictionary containing person's data with keys:
            - "FILENAME": Source filename
            - "DATA": 2D numpy array of time-series data
            - "COLUMNS": List of column names
            - "MARKERS": List of marker lists for each sample
            - "FREQUENCY": Sampling frequency in Hz
        channel : str
            Name of the data channel to analyze.
        difference : str
            Minimum time difference between detected features as time string
            (e.g., "10s", "500ms").
        prominence : int or float
            Minimum prominence of peaks/valleys.
        height : int or float
            Minimum height of peaks/valleys (0 to disable).
        format : str
            Detection mode: "MAX" for peaks, "MIN" for valleys.
        overwrite: bool
            If you want to delete all previous markers before adding new ones.

        Returns
        -------
        dict[str, any]
            Updated person dictionary with detected features marked in MARKERS.
            Each detection adds the column index to the corresponding MARKERS entry.

        Notes
        -----
        - Uses scipy.signal.find_peaks for detection
        - For "MAX" mode: detects positive peaks
        - For "MIN" mode: detects negative peaks (valleys)
        - Existing markers for the channel are removed before detection
        - The difference parameter is converted to samples based on sampling frequency
        - Minimum distance is enforced to avoid detecting closely spaced features
        - Returns the person unchanged if the channel is not found
        """
        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                channel_name=channel,
                difference=difference,
                prominence=prominence,
                height=height,
                format=format,
                overwrite = overwrite
            ),
        )

        try:
            column = find_indices(channel, person["COLUMNS"])[0]
        except IndexError:
            self.print(
                "error",
                f"Could not find column '{channel}' in '{person["COLUMNS"]}', no markers for this person",
            )
            return person

        # Clear existing markers for this channel
        if overwrite:
            for marker_row in person["MARKERS"]:
                if isinstance(marker_row, list):
                    while column in marker_row:
                        marker_row.remove(column)

        # Convert time difference to samples
        difference = time_from_string(difference, person["FREQUENCY"])
        if difference <= 0:
            self.print("debug", f"Made DIFFERENCE go from {difference} to {1}")
            difference = 1
        x = person["DATA"][:, column]

        # Configure peak detection parameters
        kwargs = {}
        if height != 0:
            kwargs["height"] = height
        if prominence != 0:
            kwargs["prominence"] = prominence
        if difference != 0:
            kwargs["distance"] = difference

        # Detect features based on format
        if format == "MAX":
            peaks, _ = find_peaks(x, **kwargs)
            valleys, _ = find_peaks(-x)
        elif format == "MIN":
            peaks, _ = find_peaks(-x, **kwargs)
            valleys, _ = find_peaks(-x)

        # Add markers for detected features
        n_markers = 0
        for peak in peaks:
            person["MARKERS"][peak].append(column)
            n_markers += 1

        self.print(
            "index",
            f"Found a total of {n_markers} markers for channel {channel} for person {person["FILENAME"]}",
        )
        return person

from common import Command, copy_dict, find_indices
import numpy as np


class Partition(Command):
    """
    Partition command for segmenting data based on marker indices.

    This class inherits from Command and provides functionality to partition
    time-series data into segments based on marker columns. Each partition
    represents a contiguous block of data between marker occurrences.

    Attributes
    ----------
    index : str
        Marker column name used for partitioning boundaries.
    del_first : bool
        If True, the first partition will be removed from results.
    del_last : bool
        If True, the last partition will be removed from results.
    good : bool
        Validation status indicating whether the command is properly configured.

    Parameters
    ----------
    command : dict
        Configuration dictionary containing command parameters.
        Expected keys:
        - "index": Marker column name (str)
        - "del_first": Whether to delete first partition (bool, optional)
        - "del_last": Whether to delete last partition (bool, optional)
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize Partition command instance.

        Parameters
        ----------
        command : dict
            Configuration dictionary with command parameters.
        """
        super().__init__(command)
        self.index = command.get("index", "")
        self.del_first = command.get("del_first", False)
        self.del_last = command.get("del_last", False)
        # self.out_channel = command.get("out_channel", "")

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validates the Partition instance to ensure it meets the required criteria.

        Performs type checking, attribute validation, and size consistency checks
        for all configured parameters. Ensures the command is properly configured
        for execution.

        Returns
        -------
        bool
            True if validation passes, False otherwise.

        Notes
        -----
        Validation includes:
        1. Type checking for required attributes
        2. String case normalization
        3. Size consistency across parameter lists
        4. Base class validation
        """
        is_valid = True

        required_attributes = ["index"]
        if not self.check_type_inner(required_attributes, [str]):
            is_valid = False

        required_attributes = ["del_first", "del_last"]
        if not self.check_type_inner(required_attributes, [bool]):
            is_valid = False

        if is_valid:
            self.string_upper(["index"])

        # Ensure specified attributes have matching sizes
        try:
            self.equal_size(
                [
                    "name",
                    "resultant",
                    "index",
                    "channel",
                    "out_channel",
                    "del_first",
                    "del_last",
                ]
            )
        except ValueError as e:
            self.print("error", f"Validation failed: {e}")
            is_valid = False

        # Validate using the base class
        if not super().validate() or not is_valid:
            self.print("error", f"{self.type} class is not valid")
            return False

        self.print("debug", f"{self.type} class is valid")
        return True

    def execute(
        self, variables: dict[str, list[dict[str, any]]]
    ) -> dict[str, list[dict[str, any]]]:
        """
        Executes the Partition command on the provided variables.

        Processes each person's data, partitioning the specified channel
        based on marker indices and storing results in the output channel.

        Parameters
        ----------
        variables : dict[str, list[dict[str, any]]]
            Dictionary containing data variables to process. Keys are variable
            names, values are lists of person dictionaries.

        Returns
        -------
        dict[str, list[dict[str, any]]]
            Updated variables dictionary with partitioned data added to
            the resultant channels.

        Notes
        -----
        If the command is invalid (self.good is False), the function returns
        the input variables unchanged with a warning message.
        """
        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        for name, resultant, index, channel, out_channel, del_first, del_last in zip(
            self.name,
            self.resultant,
            self.index,
            self.channel,
            self.out_channel,
            self.del_first,
            self.del_last,
        ):
            new_people = []
            if name not in variables.keys():
                self.print("error", f"Could not find {name}")
            for person_ in variables.get(name, []):  # Safely get the list of people
                person = copy_dict(person_)
                person = self.partition(
                    person, index, channel, out_channel, del_first, del_last
                )
                new_people.append(person)
            variables[resultant] = new_people

        return variables

    def partition(
        self,
        person: dict[str, any],
        index: str,
        channel: str,
        out_channel: str,
        del_first: bool,
        del_last: bool,
    ) -> dict[str, any]:
        """
        Partition a single person's data based on marker indices.

        Parameters
        ----------
        person : dict[str, any]
            Dictionary containing person's data with keys:
            - "FILENAME": Source filename
            - "COLUMNS": List of column names
            - "DATA": 2D numpy array of data
            - "MARKERS": List of marker rows
        index : str
            Column name containing partition markers.
        channel : str
            Column name to partition.
        out_channel : str
            Key to store partitioned results in person dictionary.
        del_first : bool
            If True, remove the first partition.
        del_last : bool
            If True, remove the last partition.

        Returns
        -------
        dict[str, any]
            Updated person dictionary with partitioned data stored under
            out_channel key.

        Notes
        -----
        Partitions are created by splitting the channel data at rows where
        the marker column contains a marker value. Empty partitions are
        filtered based on del_first and del_last parameters.
        """
        self.print(
            "debug",
            f"{self.type} of {person['FILENAME']} - ",
            self.debug_data(
                channel_name=channel, out_channel=out_channel, index_name=index
            ),
        )

        selected_columns = find_indices(channel, person["COLUMNS"])
        marker_columns = find_indices(index, person["COLUMNS"])
        if not selected_columns or not marker_columns:
            self.print(
                "error",
                f"could not find a column {channel} or {index} in {person["COLUMNS"]}, returning empty",
            )
            person[out_channel] = []
            return person

        selected_col = selected_columns[0]
        marker = marker_columns[0]
        self.print("index", f"'{channel}' as '{selected_col}', '{index}' as '{marker}'")

        wave = []
        waves = []
        markers = person["MARKERS"]
        for i, marker_row in enumerate(markers):
            if marker in marker_row:
                waves.append(wave)
                wave = []
            wave.append(float(person["DATA"][i, selected_col]))

        # Also save whatever is left
        if wave:
            waves.append(wave)

        if del_first:
            waves = waves[1:]
        if del_last:
            waves = waves[:-1]

        person[out_channel] = waves
        self.print("debug", f"There are a total of '{len(person[out_channel])}' waves")
        return person

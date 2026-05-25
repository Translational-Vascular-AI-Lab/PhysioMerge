from common import Command, copy_dict, find_indices


class Marker(Command):
    """
    Marker Command - Measure time intervals between markers in different channels.

    Calculates the time intervals between pairs of markers where a marker in the
    first channel is followed by a marker in the second channel. This is used to
    measure latencies, reaction times, or intervals between sequential events
    in physiological recordings.

    Attributes
    ----------
    format : str or list[str]
        Reserved parameter for future functionality (currently unused).
    channel2 : str or list[str]
        Name of the second marker channel to find after the first marker.
    good : bool
        Validation status indicating whether the command is properly configured.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize Marker command instance.

        Parameters
        ----------
        command : dict
            Configuration dictionary containing:

            - "format" : str or list[str]
                Reserved parameter (currently unused)
            - "in_channel_2" : str or list[str]
                Name of the second marker channel
            - Additional parameters inherited from Command base class:
              "name", "resultant", "channel", "out_channel"
        """
        super().__init__(command)
        # self.format = command.get("format", "")
        self.channel2 = command.get("in_channel_2", "")

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validate the Marker instance configuration.

        Performs comprehensive validation including type checking,
        size consistency checks, and base class validation.

        Returns
        -------
        bool
            True if the instance is valid, False otherwise.

        """
        is_valid = True
        # Ensure specified attributes have matching sizes
        try:
            self.equal_size(["name", "resultant", "channel", "out_channel", "channel2"])
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
        Execute the Marker command on the provided variables.

        Parameters
        ----------
        variables : dict[str, list[dict[str, any]]]
            Dictionary containing input data variables keyed by variable name.
            Each value is a list of person dictionaries containing marker data.

        Returns
        -------
        dict[str, list[dict[str, any]]]
            Dictionary with time interval results added to the output variables.
            Each result is stored as a list of single-element lists containing
            time intervals in seconds.

        Notes
        -----
        - If the command is invalid (self.good is False), returns input unchanged
        - Time intervals are measured from marker in channel to next marker in channel2
        - If no matching marker pairs are found, returns empty list
        - Multiple marker interval measurements can be performed simultaneously
          by providing arrays for parameters
        """
        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        for name, resultant, channel, out_channel, channel2 in zip(
            self.name, self.resultant, self.channel, self.out_channel, self.channel2
        ):
            new_people = []
            if name not in variables:
                self.print(
                    "error", f"the variable name {name} is not in {variables.keys()}"
                )
            for person_ in variables.get(name):
                person = copy_dict(person_)
                person = self.marker_compare(person, channel, out_channel, channel2)
                new_people.append(person)
            variables[resultant] = new_people

        return variables

    def marker_compare(
        self, person: dict[str, any], channel: str, out_channel: str, channel2: str
    ) -> dict[str, any]:
        """
        Measure time intervals between markers in two channels.

        Parameters
        ----------
        person : dict[str, any]
            Dictionary containing person's data with keys:
            - "FILENAME": Source filename
            - "COLUMNS": List of column names
            - "MARKERS": List of marker lists for each sample
            - "FREQUENCY": Sampling frequency in Hz
        channel : str
            Name of the first marker channel (trigger/start event).
        out_channel : str
            Name of the output channel for time interval results.
        channel2 : str
            Name of the second marker channel (response/end event).

        Returns
        -------
        dict[str, any]
            Updated person dictionary with time intervals stored under out_channel.
            Results are stored as a list of single-element lists, each containing
            a time interval in seconds.

        Notes
        -----
        - Algorithm finds pairs where a marker in `channel` is followed by
          a marker in `channel2`
        - Time is measured in samples from the first marker to the second marker,
          then converted to seconds using the sampling frequency
        - If a marker in `channel2` occurs before any marker in `channel`,
          it is ignored
        - After finding a marker pair, the search resets to look for the next
          marker in `channel`
        - If either channel is not found in COLUMNS, returns empty list
        - Time intervals are calculated as: samples / frequency (seconds)
        """
        self.print(
            "debug",
            f"{self.type} of {person['FILENAME']} - ",
            self.debug_data(
                first_channel_name=channel,
                second_channel_name=channel,
                out_channel=channel2,
            ),
        )

        if channel not in person["COLUMNS"]:
            self.print("error", f"Channel 1 is missing from known channels")
        if channel2 not in person["COLUMNS"]:
            self.print("error", f"Channel 2 is missing from known channels")
        marker1 = find_indices(channel, person["COLUMNS"])[0]
        marker2 = find_indices(channel2, person["COLUMNS"])[0]
        if not marker1 or not marker2:
            self.print(
                "error",
                f"could not find a column {channel} or {channel2} in {person["COLUMNS"]}, returning empty",
            )
            person[out_channel] = []
            return person
        self.print(
            "index",
            f"{channel} as {marker1}, and {channel2} as {marker2}.",
        )

        differences = []
        markers = person["MARKERS"]
        found_mark1 = False
        time = float("inf")
        for i, marker_row in enumerate(markers):
            if marker1 in marker_row:
                found_mark1 = True
                time = 0
            if found_mark1:
                time += 1
                if marker2 in marker_row:
                    found_mark1 = False
                    if time > 0:
                        time = time - 1
                    differences.append([time / person["FREQUENCY"]])
                    time = float("inf")

        self.print("index", f"differences {differences}")

        person[out_channel] = differences
        return person

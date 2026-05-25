from common import Command, copy_dict, time_from_string


class Slice(Command):
    """
    Slice Command - Percentage-based data segment extraction.

    The Slice command extracts specified percentage ranges from data segments.
    For each segment in the input channel, it calculates start and end indices
    based on percentage values and extracts the corresponding subsegment.

    Attributes
    ----------
    start : float
        Starting percentage (0.0 to 1.0) of each segment to include.
    end : float
        Ending percentage (0.0 to 1.0) of each segment to include.
    good : bool
        Validation status indicating whether the command is properly configured.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize Slice command instance.

        Parameters
        ----------
        command : dict
            Configuration dictionary containing command parameters.
            Expected keys:

            - "name" : list[str]
                Names of input variables containing data
            - "resultant" : list[str]
                Names of output variables for storing results
            - "channel" : list[str]
                Names of channels to slice from input data
            - "out_channel" : list[str]
                Names of channels to store sliced results
            - "start" : list[float]
                Starting percentage (0.0 to 1.0) of each segment to include
            - "end" : list[float]
                Ending percentage (0.0 to 1.0) of each segment to include
        """
        super().__init__(command)
        self.start = command.get("start", 0.0)
        self.end = command.get("end", 0.0)

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validate the Slice command instance.

        Ensures that required attributes are present, of correct types,
        and that array sizes match expectations.

        Returns
        -------
        bool
            True if the command is valid, False otherwise.

        Notes
        -----
        Validation includes:
        1. Type checking for start and end parameters
        2. Size consistency across parameter lists
        3. Base class validation
        """
        is_valid = True

        required_flt = ["start", "end"]
        if not self.check_type_inner(required_flt, [float]):
            is_valid = False

        try:
            self.equal_size(
                ["name", "channel", "resultant", "out_channel", "start", "end"]
            )
        except ValueError as e:
            self.print("error", f"Validation failed: {e}")
            is_valid = False

        if is_valid:
            self.string_upper(["name", "channel", "resultant", "out_channel"])

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
        Execute the Slice command on the provided variables.

        Processes each person's data, extracting percentage-based slices
        from the specified channels and storing results in output channels.

        Parameters
        ----------
        variables : dict[str, list[dict[str, any]]]
            Dictionary containing data variables to process.
            Keys are variable names, values are lists of person dictionaries.

        Returns
        -------
        dict[str, list[dict[str, any]]]
            Updated variables dictionary with sliced data added to
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
        for name, resultant, channel, out_channel, start, end in zip(
            self.name,
            self.resultant,
            self.channel,
            self.out_channel,
            self.start,
            self.end,
        ):
            new_people = []
            if variables.get(name) == None:
                self.print("error", f"name does not exist, name given '{name}")
                continue
            for person_ in variables.get(name):
                if person_ == None:
                    self.print("error", "Got an None Person")
                    continue
                person = copy_dict(person_)
                person = self.measurement(person, channel, out_channel, start, end)
                new_people.append(person)
            variables[resultant] = new_people

        return variables

    def measurement(
        self,
        person: dict[str, any],
        channel: str,
        out_channel: str,
        start: float,
        end: float,
    ) -> dict[str, any]:
        """
        Perform percentage-based slicing on a single person's channel data.

        Parameters
        ----------
        person : dict[str, any]
            Dictionary containing person's data with keys:
            - "FILENAME": Source filename
            - channel: List of data segments to slice
        channel : str
            Key name of the input channel containing segments to slice.
        out_channel : str
            Key name to store sliced results in person dictionary.
        start : float
            Starting percentage (0.0 to 1.0) of each segment to include.
        end : float
            Ending percentage (0.0 to 1.0) of each segment to include.

        Returns
        -------
        dict[str, any]
            Updated person dictionary with sliced data stored under
            out_channel key.

        Notes
        -----
        - Percentages are automatically clamped to [0.0, 1.0]
        - If start > end, an error is printed but processing continues
        - If channel contains empty data, a warning is printed
        - Each segment is sliced independently
        """
        self.print(
            "debug",
            f"{self.type} of {person['FILENAME']} - ",
            self.debug_data(channels=channel, start=start, end=end),
        )

        sliced = []

        if channel not in person:
            self.print(
                "error",
                f"Channel {channel} could not be found for {person['FILENAME']}",
            )
            return person

        if start > end:
            self.print("error", "starting percentage is bigger than end")

        if not person[channel]:
            self.print("warning", f"empty data channel for {person["FILENAME"]}")

        for row in person[channel]:
            length = len(row)
            start = max(0.0, min(1.0, start))
            end = max(0.0, min(1.0, end))

            # Take first X% (start)
            n_start = int(length * start)
            n_end = int(length * end)

            sliced.append(row[n_start:n_end])

        person[out_channel] = sliced
        return person

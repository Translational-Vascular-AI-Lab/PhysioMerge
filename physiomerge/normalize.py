from common import Command, copy_dict, time_from_string


class Normalize(Command):
    """
    Normalize Command - Min-max scaling of data segments.

    Performs min-max normalization on data segments, scaling values to a specified
    range using the formula:

        x_norm = height * (x - min) / (max - min) + shift

    Where:
        x = original value
        min = minimum value in segment
        max = maximum value in segment
        height = desired range height
        shift = offset/base value

    Attributes
    ----------
    height : int or float
        Scaling factor that determines the range of normalized values.
        Defines the height of the output range.
    shift : int or float
        Offset added to normalized values, determining the base level.
        Defines the minimum value of the output range.
    good : bool
        Validation status indicating whether the command is properly configured.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize Normalize command instance.

        Parameters
        ----------
        command : dict
            Configuration dictionary containing command parameters.
            Expected keys:

            - "name" : list[str]
                Names of input variables containing data
            - "resultant" : list[str]
                Names of output variables for storing normalized data
            - "channel" : list[str]
                Names of input channels to normalize
            - "out_channel" : list[str]
                Names of output channels for normalized data
            - "height" : list[float] or list[int]
                Desired range height after normalization
            - "shift" : list[float] or list[int]
                Base value/offset after normalization
        """
        super().__init__(command)
        self.height = command.get("height", 1)
        self.shift = command.get("shift", 0)

        self.good = False

    def validate(self) -> bool:
        """
        Validate the Normalize command instance.

        Ensures that required attributes are present, of correct types,
        and that array sizes match expectations.

        Returns
        -------
        bool
            True if the command is valid, False otherwise.

        Notes
        -----
        Validation includes:
        1. Type checking for height and shift parameters (must be int or float)
        2. Size consistency across parameter lists
        3. Base class validation
        """
        is_valid = True

        required_int = ["height", "shift"]
        if not self.check_type_inner(required_int, [int, float]):
            is_valid = False
            self.print("error", "Height or Shift is not an int")

        self.equal_size(
            ["name", "channel", "resultant", "out_channel", "height", "shift"]
        )

        if not super().validate() or not is_valid:
            self.print("error", f"{self.type} class is not valid")
            return False

        self.print("debug", f"{self.type} class is valid")
        return True

    def execute(self, variables: dict[str, list[dict]]) -> dict[str, list[dict]]:
        """
        Execute the Normalize command on the provided variables.

        Processes each person's data, applying min-max normalization to the
        specified channels and storing results in output channels.

        Parameters
        ----------
        variables : dict[str, list[dict]]
            Dictionary containing data variables to process.
            Keys are variable names, values are lists of person dictionaries.

        Returns
        -------
        dict[str, list[dict]]
            Updated variables dictionary with normalized data added to
            the resultant channels.

        Notes
        -----
        If the command is invalid (self.good is False), the function returns
        the input variables unchanged with a warning message.
        """
        self.good = self.validate()

        if not self.good:
            print("error", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        for name, channel, resultant, out_channel, height, shift in zip(
            self.name,
            self.channel,
            self.resultant,
            self.out_channel,
            self.height,
            self.shift,
        ):
            new_people = []
            if name not in variables:
                self.print("error", f"Variable with name '{name}' not found")
                continue

            for person_ in variables.get(name):
                person = copy_dict(person_)
                person = self.normalize(person, channel, out_channel, height, shift)
                new_people.append(person)
            variables[resultant] = new_people
        return variables

    def normalize(
        self,
        person: dict[str, any],
        channel: str,
        out_channel: str,
        height: int | float,
        shift: int | float,
    ) -> dict[str, any]:
        """
        Apply min-max normalization to a single person's channel data.

        Parameters
        ----------
        person : dict[str, any]
            Dictionary containing person's data with keys:
            - "FILENAME": Source filename
            - channel: List of data segments to normalize
        channel : str
            Key name of the input channel containing segments to normalize.
        out_channel : str
            Key name to store normalized results in person dictionary.
        height : int or float
            Desired range height after normalization.
            For example: height=1 gives range [shift, shift+1]
        shift : int or float
            Base value/offset after normalization.
            For example: shift=0 gives range starting at 0

        Returns
        -------
        dict[str, any]
            Updated person dictionary with normalized data stored under
            out_channel key.

        Notes
        -----
        - Normalization is applied independently to each segment
        - If a segment has constant values (max == min), values are copied unchanged
        - All output values are converted to floats
        - The normalization formula is: (height * (value - min) / (max - min)) + shift
        """
        self.print(
            "debug",
            f"{self.type} of {person['FILENAME']} - ",
            self.debug_data(
                channel_name=channel,
                out_channel=out_channel,
                height=height,
                shift=shift,
            ),
        )

        new_data = []
        for i, row in enumerate(person[channel]):
            new_row = []
            if row:
                max_val, min_val = max(row), min(row)
                for n in row:
                    if max_val == min_val:
                        new_row.append(float(n))  # Ensure float conversion
                        continue
                    new_row.append(
                        float(height) * (n - min_val) / (max_val - min_val)
                        + float(shift)
                    )
            new_data.append(new_row)

        person[out_channel] = [[float(item) for item in row] for row in new_data]

        return person

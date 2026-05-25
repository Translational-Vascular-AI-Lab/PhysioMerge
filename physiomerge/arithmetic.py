from common import Command, copy_dict


class Arithmetic(Command):
    """
    Arithmetic Command - Perform element-wise arithmetic operations on data channels.

    Applies mathematical operations to each element in data channels, supporting
    both channel-to-channel operations and channel-to-constant operations.
    Operations are applied element-wise across segments and within segments.

    Attributes
    ----------
    format : str
        Arithmetic operation to perform. Options: "+", "-", "*", "/", "^", "-1"
    channel2 : str
        Name of the second channel for channel-to-channel operations.
        If empty, operation uses a constant number.
    number : int, float, or None
        Constant value for channel-to-constant operations.
        Used when channel2 is not specified.
    using_channel2 : bool
        Flag indicating whether operation uses a second channel (True)
        or a constant number (False).
    good : bool
        Validation status indicating whether the command is properly configured.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize Arithmetic command instance.

        Parameters
        ----------
        command : dict
            Configuration dictionary containing:

            - "format" : str
                Arithmetic operation: "+" (add), "-" (subtract), "*" (multiply),
                "/" (divide), "^" (power), "-1" (reciprocal)
            - "channel2" : str, optional
                Name of second channel for channel-to-channel operations.
                If not provided, "num" must be specified.
            - "num" : int or float, optional
                Constant number for channel-to-constant operations.
                Required if channel2 is not specified.
            - Additional parameters inherited from Command base class:
              "name", "resultant", "channel", "out_channel"
        """
        super().__init__(command)
        self.format = command.get("format", "")  # .lower()
        self.channel2 = command.get("in_channel_2", "")  # .lower()
        self.number = command.get("num", None)  # Can be None

        self.using_channel2 = bool(self.channel2)

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validate the Arithmetic instance configuration.

        Performs comprehensive validation including type checking, format validation,
        operand validation, size consistency checks, and base class validation.

        Returns
        -------
        bool
            True if the instance is valid, False otherwise.

        Notes
        -----
        Validation includes:
        1. Type checking for format and operands
        2. Format validation against allowed arithmetic operations
        3. Operand validation (either channel2 or number must be valid)
        4. Size consistency across parameter lists
        5. Base class validation
        """
        is_valid = True

        if not self.check_type_inner(["format"], [str]):
            is_valid = False

        if self.using_channel2:
            if not self.check_type_inner(["channel2"], [str]):
                is_valid = False
        else:
            if not self.check_type_inner(["number"], [int, float]):
                is_valid = False

        # Validate format
        valid_formats = ["+", "-", "*", "/", "^", "-1"]
        if not self.is_in_array(self.format, valid_formats):
            is_valid = False

        self.string_upper(["format", "channel2"])

        # ensure specified attributes have matching sizes
        try:
            required_fields = ["name", "resultant", "channel", "out_channel", "format"]
            if self.using_channel2:
                required_fields.append("channel2")
            else:
                required_fields.append("number")
            self.equal_size(required_fields)
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
        Execute the Arithmetic command on the provided variables.

        Parameters
        ----------
        variables : dict[str, list[dict[str, any]]]
            Dictionary containing input data variables keyed by variable name.
            Each value is a list of person dictionaries containing channel data.

        Returns
        -------
        dict[str, list[dict[str, any]]]
            Dictionary with arithmetic results added to the output variables.
            Each result maintains the same segment structure as input.

        Notes
        -----
        - If the command is invalid (self.good is False), returns input unchanged
        - Operations are applied element-wise within each segment
        - For channel-to-channel operations, corresponding segments must have
          the same length
        - Division by zero results in NaN values
        - Empty input channels result in NaN output
        """
        self.good = self.validate()
        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print(
            "command", f"Running the {self.type} command in format '{self.format}'"
        )

        iterable = zip(
            self.name,
            self.resultant,
            self.channel,
            self.out_channel,
            self.channel2 if self.using_channel2 else self.number,
            self.format,
        )

        for name, resultant, channel, out_channel, operand, format in iterable:
            new_people = []
            if name not in variables:
                self.print("error", f"Variable with name '{name}' not found")
            for person_ in variables.get(name, []):
                person = copy_dict(person_)
                person = self.adjust_channel(
                    person, channel, out_channel, operand, format
                )
                new_people.append(person)
            variables[resultant] = new_people

        return variables

    def adjust_channel(
        self,
        person: dict[str, any],
        channel: str,
        out_channel: str,
        operand: any,
        format: str,
    ) -> dict[str, any]:
        """
        Apply arithmetic operation to a single person's data channel.

        Parameters
        ----------
        person : dict[str, any]
            Dictionary containing person's data with keys:
            - "FILENAME": Source filename
            - channel: List of data segments to operate on
            - operand: Either channel name (for channel-to-channel) or
              constant value (for channel-to-constant)
        channel : str
            Name of the primary input channel.
        out_channel : str
            Name of the output channel for arithmetic results.
        operand : any
            Either a string (channel name) or numeric constant,
            depending on operation type.

        Returns
        -------
        dict[str, any]
            Updated person dictionary with arithmetic results stored under out_channel.
            Results maintain the same segment structure as input.

        Notes
        -----
        - For channel-to-channel operations ("+", "-", "*", "/"):
          Corresponding segments from both channels must have equal length
          Operation: channel1[i][j] op channel2[i][j]

        - For channel-to-constant operations ("+", "-", "*", "/"):
          Operation: channel[i][j] op constant

        - For "-1" operation (reciprocal):
          Operation: 1 / channel[i][j] (0 values become 0)
          Only works with channel-to-constant mode (ignores operand)

        - Division by zero (either in "/" or "-1") results in NaN
        - Empty segments result in NaN
        - If primary channel doesn't exist, returns empty list in out_channel
        """
        if self.using_channel2:
            debug_info = self.debug_data(
                channale_name=channel, out_channel=out_channel, second_channel=operand
            )
        else:
            debug_info = self.debug_data(
                channale_name=channel, out_channel=out_channel, number=operand
            )
        self.print("debug", f"{self.type} of {person['FILENAME']} - ", debug_info)

        if channel not in person.keys():
            self.print(
                "error",
                f"Could not find {channel} in {person.keys()} for person {person["FILENAME"]}",
            )
            person[out_channel] = []
            return person

        if len(person[channel]) == 0:
            self.print("debug", "data array was empty")
            result = [[float("NaN")]]
        else:
            if self.using_channel2:
                # Channel-to-channel operations
                operations = {
                    "+": lambda x, y: [xi + yi for xi, yi in zip(x, y)],
                    "-": lambda x, y: [xi - yi for xi, yi in zip(x, y)],
                    "*": lambda x, y: [xi * yi for xi, yi in zip(x, y)],
                    "/": lambda x, y: [
                        xi / yi if yi != 0 else float("NaN") for xi, yi in zip(x, y)
                    ],
                    "^": lambda x, y: [xi**yi for xi, yi in zip(x, y)],
                }
                result = [
                    operations[format](row, val)  # Apply operation to entire rows
                    for row, val in zip(person[channel], person[operand])
                ]
            else:
                # Channel-to-constant operations
                operations = {
                    "+": lambda x: [xi + operand for xi in x],
                    "-": lambda x: [xi - operand for xi in x],
                    "*": lambda x: [xi * operand for xi in x],
                    "/": lambda x: [
                        xi / operand if operand != 0 else float("NaN") for xi in x
                    ],
                    "-1": lambda x: [0 if xi == 0 else 1 / xi for xi in x],
                    "^": lambda x: [xi**operand for xi in x],
                }
                result = [
                    operations[format](row)  # Apply operation to entire row
                    for row in person[channel]
                ]

        person[out_channel] = result
        return person

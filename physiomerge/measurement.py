from common import Command, copy_dict, find_indices
import numpy as np
from statistics import mean, mode, median


class Measurement(Command):
    """
    Measurement Command - Calculate statistical and signal metrics on segmented data.

    Computes various measurements on each segment within a data channel, including
    statistical metrics (mean, median, mode, min, max) and signal characteristics
    (period, amplitude, frequency). Results are stored as single-element lists
    for each segment.

    Attributes
    ----------
    format : str or list[str]
        Type of measurement to perform. Can be a single format or list of formats
        for multiple operations.
    good : bool
        Validation status indicating whether the command is properly configured.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize Measurement command instance.

        Parameters
        ----------
        command : dict
            Configuration dictionary containing:

            - "format" : str or list[str]
                Type(s) of measurement to perform. Options:
                "mean", "mode", "median", "min", "max",
                "period", "amplitude", "frequency"
            - Additional parameters inherited from Command base class:
              "name", "resultant", "channel", "out_channel"
        """
        super().__init__(command)
        self.format = command.get("format", "")

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validate the Measurement instance configuration.

        Performs comprehensive validation including type checking, format validation,
        size consistency checks, and base class validation.

        Returns
        -------
        bool
            True if the instance is valid, False otherwise.

        Notes
        -----
        Validation includes:
        1. Type checking for format parameter(s)
        2. Format validation against allowed measurement types
        3. Size consistency across parameter lists
        4. Base class validation
        """
        is_valid = True

        required_attributes = ["format"]

        for attr_name in required_attributes:
            value = getattr(self, attr_name)
            if not isinstance(value, (str, list)):
                self.print(
                    "error",
                    f"'{attr_name}' must be a string or list, but got {type(value).__name__}.",
                )
                is_valid = False

        # Checking for valid formats
        # Check for valid formats if format is a string or list
        valid_formats = {
            "mean",
            "mode",
            "median",
            "min",
            "max",
            "period",
            "amplitude",
            "frequency",
            "delta",
        }
        if isinstance(self.format, str) and self.format not in valid_formats:
            self.print(
                "error",
                f"Invalid format '{self.format}'. Supported formats are: {', '.join(valid_formats)}.",
            )
            is_valid = False
        elif isinstance(self.format, list) and any(
            f not in valid_formats for f in self.format
        ):
            invalid_formats = [f for f in self.format if f not in valid_formats]
            self.print(
                "error",
                f"Invalid formats {invalid_formats}. Supported formats are: {', '.join(valid_formats)}.",
            )
            is_valid = False

        # Ensure specified attributes have matching sizes
        try:
            self.equal_size(["name", "resultant", "channel", "format", "out_channel"])
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
        Execute the Measurement command on the provided variables.

        Parameters
        ----------
        variables : dict[str, list[dict[str, any]]]
            Dictionary containing input data variables keyed by variable name.
            Each value is a list of person dictionaries containing segmented data.

        Returns
        -------
        dict[str, list[dict[str, any]]]
            Dictionary with measurement results added to the output variables.
            Each result is stored as a list of single-element lists, one per segment.

        Notes
        -----
        - If the command is invalid (self.good is False), returns input unchanged
        - Each segment in the input channel is measured independently
        - Results for empty segments are set to [0]
        - For "period", "amplitude", and "frequency", calculations use the
          segment's properties and sampling frequency
        """
        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        for name, resultant, channel, out_channel, format in zip(
            self.name, self.resultant, self.channel, self.out_channel, self.format
        ):
            new_people = []
            if name not in variables:
                self.print(
                    "error", f"the variable name {name} is not in {variables.keys()}"
                )
            for person_ in variables.get(name):
                person = copy_dict(person_)
                person = self.measurement(person, channel, out_channel, format)
                new_people.append(person)
            variables[resultant] = new_people

        return variables

    def measurement(
        self, person: dict[str, any], channel: str, out_channel: str, format: str
    ) -> dict[str, any]:
        """
        Perform measurement operation on a single person's data channel.

        Parameters
        ----------
        person : dict[str, any]
            Dictionary containing person's data with keys:
            - "FILENAME": Source filename
            - "FREQUENCY": Sampling frequency in Hz
            - channel: List of data segments to measure
        channel : str
            Name of the input channel containing segments to measure.
        out_channel : str
            Name of the output channel for measurement results.
        format : str
            Type of measurement to perform. Options:

            - Statistical metrics:
              * "mean": Arithmetic mean of segment values
              * "median": Median value of segment
              * "mode": Most frequent value in segment
              * "min": Minimum value in segment
              * "max": Maximum value in segment

            - Signal characteristics:
              * "period": Segment duration in seconds (len(segment) / frequency)
              * "amplitude": Peak-to-peak amplitude (max - min)
              * "frequency": Segment frequency in Hz (frequency / len(segment))
              * "delta": The difference between the Ending value, and Starting value (end-start)
        Returns
        -------
        dict[str, any]
            Updated person dictionary with measurement results stored under out_channel.
            Results are stored as a list of single-element lists, one per segment.

        Raises
        ------
        ValueError
            If an unsupported format is specified.

        Notes
        -----
        - Each segment is measured independently
        - Empty segments return [0] as the measurement result
        - For "period" and "frequency", the sampling frequency from person["FREQUENCY"]
          is used in calculations
        - The "mode" function uses statistics.mode, which may raise StatisticsError
          if there is no unique mode
        """
        
        self.print(
            "debug",
            f"{self.type} of {person['FILENAME']} - ",
            self.debug_data(
                channale_name=channel,
                out_channel=out_channel,
                measurement_format=format,
            ),
        )
        if channel not in person:
            self.print(
                "error",
                f"Could not find channel {channel} in {person["FILENAME"]}, we have {person.keys()}",
            )
        if not person[channel]:
            self.print("warning", f"empty data channel for {person["FILENAME"]}")

        # Define format-to-function mapping
        format_functions = {
            "mean": mean,
            "mode": mode,
            "median": median,
            "min": min,
            "max": max,
            "period": lambda row: len(row) / person["FREQUENCY"],
            "amplitude": lambda row: max(row) - min(row),
            "frequency": lambda row: person["FREQUENCY"] / len(row),
            "delta": lambda row: row[-1]-row[0],
        }

        if format not in format_functions:
            raise ValueError(
                f"Invalid format '{format}'. Supported formats are: {', '.join(format_functions.keys())}"
            )

        # Perform measurement
        output = [
            [format_functions[format](row)] if row else [0] for row in person[channel]
        ]

        person[out_channel] = output
        self.print(
            "index",
            f"Output of {person["FILENAME"]} has {len(output)} values saved in {out_channel}",
        )
        return person

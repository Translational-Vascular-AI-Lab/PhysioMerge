"""
Check Command Module

This module provides the Check class for validating data quality and applying
conditional checks to data channels with various comparison operations.
"""

import sys
import os
import numpy as np

from common import Command, copy_dict, find_indices, time_from_string


class Check(Command):
    """
    A command class for performing conditional checks on data channels.

    This class extends the Command base class to provide data validation functionality.
    It supports various statistical measures, comparison operators, and can check
    both absolute values and percentages of values.

    Attributes:
        format (str): Specifies whether to check the value itself ("Y") or its
            position/index ("X").
        variable (str): The statistical measure to evaluate. One of: "MAX", "MIN",
            "MEAN", "MEDIAN", "START", "END", "AMP", "FLAT".
        compare (str): Comparison operator to use. One of: ">", "<", ">=", "<=",
            "==", "!=", "%x>", "%x<", "%x>=", "%x<=", "%x==", "%x!=".
        num (float | int | list): The threshold value(s) to compare against.
        time (str): Optional time string that can be converted to a number using
            frequency information.
        alright (str): Name of the mask channel to update based on check results.
        good (bool): Validation status of the command instance.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize a Check command instance.

        Args:
            command (dict): Configuration dictionary containing:
                - format (str): Check format ("X" or "Y")
                - variable (str): Statistical variable to check
                - compare (str): Comparison operator
                - num (float|int|list): Threshold value(s)
                - time (str): Optional time specification
                - mask (str): Mask channel name (stored as 'alright')
                - Additional parameters inherited from Command base class
        """
        super().__init__(command)
        self.format = command.get("format", "")
        self.variable = command.get("variable", "")
        self.compare = command.get("compare", "")
        self.num = command.get("num", 0)
        self.time = command.get("time", "")
        self.alright = command.get("mask", "")

        self.good = False

    def validate(self) -> bool:
        """
        Validate the Check instance configuration.

        Performs comprehensive validation including type checking, value validation
        against allowed sets, and size consistency checks.

        Returns:
            bool: True if the instance is valid, False otherwise.

        Note:
            Automatically converts string parameters to uppercase for validation.
        """
        is_valid = True

        required_attributes = ["alright", "format", "compare", "variable", "time"]
        if not self.check_type_inner(required_attributes, [str]):
            is_valid = False

        if is_valid:
            self.string_upper(["alright", "format", "compare", "variable"])

        required_attributes = ["num"]
        if not self.check_type_inner(required_attributes, [float, int]):
            is_valid = False

        valid_variable = {
            "MAX",
            "MIN",
            "MEAN",
            "MEDIAN",
            # "MODE",
            "START",
            "END",
            "AMP",
            "FLAT",
        }
        if not self.is_in_array(self.variable, valid_variable):
            is_valid = False

        valid_format = {"X", "Y"}
        if not self.is_in_array(self.format, valid_format):
            is_valid = False

        valid_compare = {
            "<",
            ">",
            "<=",
            ">=",
            "==",
            "!=",
            "%X<",
            "%X>",
            "%X<=",
            "%X>=",
            "%X==",
            "%X!=",
            # "%y<",
            # "%y>",
            # "%y<=",
            # "%y>=",
            # "%y==",
            # "%y!=",
        }
        if not self.is_in_array(self.compare, valid_compare):
            is_valid = False

        if not isinstance(self.num, (float, int, list)):
            self.print(
                "error", f"'num' must be a number, but got {type(self.num).__name__}."
            )
            is_valid = False

        # ensure specified attributes have matching sizes
        try:
            self.equal_size(
                [
                    "name",
                    "resultant",
                    "channel",
                    "alright",
                    "num",
                    "time",
                    "compare",
                    "variable",
                    "format",
                ]
            )
        except ValueError as e:
            self.print("error", f"Validation failed: {e}")
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
        Execute the Check command on the provided variables.

        Iterates through all persons in the specified input variables, applying
        the check condition to each data row and updating the mask channel accordingly.

        Args:
            variables (dict[str, list[dict[str, any]]]): Dictionary containing
                input data variables keyed by variable name.

        Returns:
            dict[str, list[dict[str, any]]]: Dictionary with updated mask channels
                in the output variables.

        Note:
            If the command is invalid, it will be skipped and variables returned unchanged.
        """
        self.good = self.validate()

        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        for (
            name,
            resultant,
            channel,
            alright,
            num,
            time,
            variable,
            format,
            compare,
        ) in zip(
            self.name,
            self.resultant,
            self.channel,
            self.alright,
            self.num,
            self.time,
            self.variable,
            self.format,
            self.compare,
        ):
            if name not in variables:
                self.print(
                    "error", f"the variable name {name} is not in {variables.keys()}"
                )
            new_people = []
            for person_ in variables.get(name):
                person = copy_dict(person_)
                if time:
                    num = time_from_string(time, person["FREQUENCY"])
                person = self.check_single(
                    person, channel, alright, num, variable, format, compare, name
                )
                new_people.append(person)
            variables[resultant] = new_people

        return variables

    def check_single(
        self,
        person: dict[str, any],
        channel: str,
        alright: str,
        num: float | int,
        variable: str,
        format: str,
        compare: str,
        name: str,
    ) -> dict[str, any]:
        """
        Perform the check operation on a single person's data.

        Applies the specified statistical measure and comparison to each row of data,
        updating the mask channel to indicate which rows pass the check.

        Args:
            person (dict[str, any]): Dictionary containing person's data channels.
            channel (str): Name of the input channel to check.
            alright (str): Name of the mask channel to update.
            num (float | int): Threshold value to compare against.
            variable (str): Statistical measure to evaluate.
            format (str): Whether to check value ("Y") or position ("X").
            compare (str): Comparison operator.
            name (str): Name of the variable being processed.

        Returns:
            dict[str, any]: Updated person dictionary with mask channel modified.
        """

        def find_longest_flat_region(signal, tolerance=0.1):
            """
            Find the longest flat region in a signal.

            Args:
                signal: Input signal (1D numpy array)
                tolerance: Maximum difference between values to consider them equal

            Returns:
                int: Length of the longest flat region (in samples)
            """
            if len(signal) == 0:
                return 0

            # Initialize variables to track the longest flat region
            longest_length = 1
            current_length = 1
            longest_value = signal[0]
            longest_start = 0
            current_start = 0

            for i in range(1, len(signal)):
                # Check if current value is approximately equal to previous value
                if np.abs(signal[i] - signal[i - 1]) <= tolerance:
                    current_length += 1
                else:
                    if current_length > longest_length:
                        longest_length = current_length
                        longest_value = signal[i - 1]
                        longest_start = current_start
                    current_length = 1
                    current_start = i

            # Check one last time in case the longest region is at the end
            if current_length > longest_length:
                longest_length = current_length
                longest_value = signal[-1]
                longest_start = current_start

            return longest_length

        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                channal_name=channel,
                alright_mask=alright,
                value=variable,
                number=num,
                format=format,
                comparision=compare,
            ),
        )

        # Filter the data using 'alright' mask
        if channel not in person.keys():
            self.print(
                "error", f"Person does not contain '{channel}' in their {person.keys()}"
            )

        person[alright] = self.ensure_alright(person, channel, alright)

        alright_data = person[alright]

        condition_lambda = {
            ">": lambda val, row: val > num,
            "<": lambda val, row: val < num,
            ">=": lambda val, row: val >= num,
            "<=": lambda val, row: val <= num,
            "==": lambda val, row: val == num,
            "!=": lambda val, row: val != num,
            "%X>": lambda val, row: val / len(row) > num,
            "%X<": lambda val, row: val / len(row) < num,
            "%X>=": lambda val, row: val / len(row) >= num,
            "%X<=": lambda val, row: val / len(row) <= num,
            "%X==": lambda val, row: val / len(row) == num,
            "%X!=": lambda val, row: val / len(row) != num,
            "%Y>": lambda val, row: val / max(row) > num,
            "%Y<": lambda val, row: val / max(row) < num,
            "%Y>=": lambda val, row: val / max(row) >= num,
            "%Y<=": lambda val, row: val / max(row) <= num,
            "%Y==": lambda val, row: val / max(row) == num,
            "%Y!=": lambda val, row: val / max(row) != num,
        }
        value_lambda = {
            "MAX": lambda row: np.nanmax(row, axis=0).tolist(),
            "MIN": lambda row: np.nanmin(row, axis=0).tolist(),
            "MEAN": lambda row: np.nanmean(row, axis=0).tolist(),
            "MEDIAN": lambda row: np.nanmedian(row, axis=0).tolist(),
            "START": lambda row: row[0],
            "END": lambda row: row[-1],
            "AMP": lambda row: (
                np.nanmax(row, axis=0) - np.nanmin(row, axis=0)
            ).tolist(),
            "FLAT": lambda row: find_longest_flat_region(row),
        }

        bad_waves = 0
        for i, row in enumerate(person[channel]):
            good = True
            value = -1
            try:
                value = value_lambda[variable](row)
                if format == "X":
                    if variable == "START":
                        value = 0
                    elif variable == "END":
                        value = len(row)
                    else:
                        value = row.index(value)
                # self.print("index", f"value = {value}")

                # good = checks[self.format](row)

                good = condition_lambda[compare](value, row)
                self.print("index", f"row '{i}' was found as '{good}' with value {value}")
            except (ValueError, IndexError):  # Handle empty or invalid rows
                self.print("index", f"row '{i}' was had an error")
                good = False

            if good:
                alright_data[i] *= 1
            else:
                bad_waves += 1
                alright_data[i] = 0

        person[alright] = alright_data
        self.print("debug", f"Checked rows for {self.format} on {num}")
        self.print(
            "debug",
            f"Found {bad_waves} bad rows, with total of {len(alright_data)-sum(alright_data)}",
        )
        if sum(alright_data) == 0:
            self.print(
                "warning",
                f"Person {person['FILENAME']} has no valid waves",
                self.debug_data(
                    channal_name=channel,
                    alright_mask=alright,
                    value=variable,
                    number=num,
                    format=format,
                    comparision=compare,
                    var_name=name,
                ),
            )
        return person

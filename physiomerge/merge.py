"""
Merge Command Module

This module provides the Merge class for combining or comparing data from two
channels using various logical and comparison operations.
"""

import numpy as np
from scipy.stats import mode

from common import Command, copy_dict, time_from_string


class Merge(Command):
    """
    A command class for merging or comparing data from two channels.

    This class extends the Command base class to provide functionality for
    combining data from two channels using logical operations (AND, OR, etc.),
    or selecting between them based on length comparisons (greater, lesser).

    Attributes:
        channel2 (str | list): Name of the second channel to merge with.
        format (str | list): Operation to apply when merging channels.
        good (bool): Validation status of the command instance.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize a Merge command instance.

        Args:
            command (dict): Configuration dictionary containing:
                - channel2 (str|list): Name of second channel
                - format (str|list): Merge operation to apply
                - Additional parameters inherited from Command base class:
                  name, channel, resultant, out_channel
        """
        super().__init__(command)
        self.channel2 = command.get("in_channel_2", "")
        self.format = command.get("format", "")

        self.good = False

    def validate(self) -> bool:
        """
        Validate the Merge instance configuration.

        Performs validation including type checking, operation validation,
        and ensures all parameter lists have matching sizes.

        Returns:
            bool: True if the instance is valid, False otherwise.
        """
        is_valid = True

        required_str = ["channel2", "format"]
        if not self.check_type_inner(required_str, [str]):
            is_valid = False

        if is_valid:
            self.string_upper(["channel2", "format"])

        self.equal_size(
            ["name", "channel", "resultant", "out_channel", "channel2", "format"]
        )

        for form in self.format:
            if form not in [
                "GREATER",
                "LESSER",
                "AND",
                "OR",
                "NAND",
                "NOR",
                "XOR",
                "XNOR",
            ]:
                self.print("error", f"'{form}' is not a valid format for {self.type}")
                is_valid = False

        if not super().validate() or not is_valid:
            self.print("error", f"{self.type} class is not valid")
            return False

        self.print("debug", f"{self.type} class is valid")
        return True

    def execute(self, variables: dict[str, list[dict]]) -> dict[str, list[dict]]:
        """
        Execute the Merge command on the provided variables.

        Iterates through all persons in the specified input variables, applying
        the merge operation to pairs of channels and storing results in output
        channels.

        Args:
            variables (dict[str, list[dict]]): Dictionary containing input data
                variables keyed by variable name.

        Returns:
            dict[str, list[dict]]: Dictionary with merged results in the
                output variables.

        Note:
            If the command is invalid, it will be skipped and variables returned
            unchanged.
        """
        self.good = self.validate()

        if not self.good:
            print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        for name, channel, resultant, out_channel, channel2, form in zip(
            self.name,
            self.channel,
            self.resultant,
            self.out_channel,
            self.channel2,
            self.format,
        ):
            new_people = []
            if name not in variables:
                self.print(
                    "error", f"the variable name {name} is not in {variables.keys()}"
                )
            for person_ in variables.get(name):
                person = copy_dict(person_)
                person = self.merge(person, channel, channel2, out_channel, form)
                new_people.append(person)
            variables[resultant] = new_people
        return variables

    def merge(
        self,
        person: dict[str, any],
        channel: str,
        channel2: str,
        out_channel: str,
        form: str,
    ) -> dict[str, any]:
        """
        Merge data from two channels using the specified operation.

        Applies the merge operation to combine or compare data from two
        channels, storing the result in the output channel.

        Args:
            person (dict[str, any]): Dictionary containing person's data channels.
            channel (str): Name of the first input channel.
            channel2 (str): Name of the second input channel.
            out_channel (str): Name of the output channel for merged result.
            form (str): Merge operation to apply.

        Returns:
            dict[str, any]: Updated person dictionary with merged result in
                out_channel.

        Note:
            - For logical operations (AND, OR, etc.), channels must be same length
            - For length comparisons (greater, lesser), selects entire list
            - If both channels are empty, logs a warning
            - Result length depends on operation type
        """
        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                channel_name=channel,
                second_channel_name=channel2,
                out_channel=out_channel,
                format=form,
            ),
        )
        if channel not in person:
            self.print("error", f"the channel name {channel} is not in {person.keys()}")
        if channel2 not in person:
            self.print(
                "error", f"the channel name {channel2} is not in {person.keys()}"
            )

        if len(person[channel]) == 0 and len(person[channel2]) == 0:
            self.print(
                "warning",
                f"No data was found for either channel for '{person["FILENAME"]}'",
            )

        self.print("index", f"length channel '{len(person[channel])}' ")
        self.print("index", f"length channel2 '{len(person[channel2])}' ")

        # Helper function to convert boolean to 0/1
        def bool_to_int(value):
            """Convert boolean or truthy value to 0 or 1."""
            return 1 if value else 0

        operations = {
            "GREATER": lambda list1, list2: list1 if len(list1) > len(list2) else list2,
            "LESSER": lambda list1, list2: list1 if len(list1) < len(list2) else list2,
            "AND": lambda list1, list2: [
                bool_to_int(a and b) for a, b in zip(list1, list2)
            ],
            "OR": lambda list1, list2: [
                bool_to_int(a or b) for a, b in zip(list1, list2)
            ],
            "NAND": lambda list1, list2: [
                bool_to_int(not (a and b)) for a, b in zip(list1, list2)
            ],
            "NOR": lambda list1, list2: [
                bool_to_int(not (a or b)) for a, b in zip(list1, list2)
            ],
            "XOR": lambda list1, list2: [
                bool_to_int(a != b) for a, b in zip(list1, list2)
            ],
            "XNOR": lambda list1, list2: [
                bool_to_int(a == b) for a, b in zip(list1, list2)
            ],
        }

        person[out_channel] = operations[form](person[channel], person[channel2])
        self.print("index", f"length output '{len(person[out_channel])}'")
        return person

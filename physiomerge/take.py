"""
Take Command Module

This module provides the Take class for selecting subsets of data waves based on
time duration, wave count, or maximum available valid data.
"""

import numpy as np
from scipy.stats import mode

from common import Command, copy_dict, time_from_string


class Take(Command):
    """
    A command class for selecting subsets of data waves based on various criteria.

    This class extends the Command base class to provide functionality for extracting
    specific portions of data channels. It can select waves based on count, time duration,
    or maximum available valid data, with options for direction and consecutiveness.

    Attributes:
        waves (int | list): Number of waves to select (0 if using time or maximum).
        time (str | list): Time duration to select (e.g., "30s", "5m").
        alright (str | list): Name of the mask channel used to filter valid waves.
        consecutive (bool | list): Whether to require consecutive valid waves.
        direction (str | list): Direction to search for waves ("+" forward, "-" backward).
        maximum (bool | list): Whether to select maximum available valid waves.
        wave_format (bool | list): Internal flag indicating whether waves or time is used.
        good (bool): Validation status of the command instance.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize a Take command instance.

        Args:
            command (dict): Configuration dictionary containing:
                - waves (int|list): Number of waves to select
                - time (str|list): Time duration to select
                - alright (str|list): Mask channel name
                - consecutive (bool|list): Consecutive waves requirement
                - direction (str|list): Search direction ("+" or "-")
                - maximum (bool|list): Maximum waves selection flag
                - Additional parameters inherited from Command base class
        """
        super().__init__(command)
        self.waves = command.get("waves", 0)
        self.time = command.get("time", "")
        self.alright = command.get("mask", "")
        self.consecutive = command.get("consecutive", "")
        self.direction = command.get("direction", "+")
        self.maximum = command.get("maximum", False)
        self.minimum = command.get("minimum", True)

        self.wave_format = True

        self.good = False
        #self.validate()

    def validate(self) -> bool:
        """
        Validate the Take instance configuration.

        Performs comprehensive validation including type checking, value validation,
        consistency checks, and ensures at least one selection criterion is specified.

        Returns:
            bool: True if the instance is valid, False otherwise.

        Raises:
            ValueError: If parameter lists have inconsistent sizes or no valid
                selection criterion is specified.
        """
        is_valid = True

        required_str = ["time", "alright"]
        if not self.check_type_inner(required_str, [str]):
            is_valid = False

        if is_valid:
            self.string_upper(["alright"])

        required_int = ["waves"]
        if not self.check_type_inner(required_int, [int]):
            is_valid = False

        required_bool = ["consecutive", "maximum", "minimum"]
        if not self.check_type_inner(required_bool, [bool]):
            is_valid = False

        # Validate direction
        valid_formats = [
            "-",
            "+",
        ]
        if not self.is_in_array(self.direction, valid_formats):
            is_valid = False

        if is_valid:
            self.equal_size(
                [
                    "name",
                    "channel",
                    "resultant",
                    "out_channel",
                    "waves",
                    "time",
                    "maximum",
                    "direction",
                    "wave_format",
                    "consecutive",
                    "alright",
                    "minimum",
                ]
            )
            for wave_, time_, max_ in zip(self.waves, self.time, self.maximum):
                if wave_ <= 0 and time_ == "" and not max_:
                    self.print("error", f"Either waves or time should be declared.")
                    is_valid = False
                if wave_ > 0 and time_ != "":
                    self.print(
                        "warning",
                        f"Both waves and time is declared, waves takes priority",
                    )
            for i, wave_ in enumerate(self.waves):
                self.wave_format[i] = wave_ > 0

        if not super().validate() or not is_valid:
            self.print("error", f"{self.type} class is not valid")
            return False

        self.print("debug", f"{self.type} class is valid")
        return True

    def execute(self, variables: dict[str, list[dict]]) -> dict[str, list[dict]]:
        """
        Execute the Take command on the provided variables.

        Iterates through all persons in the specified input variables, selecting
        subsets of waves based on the configured criteria and storing results
        in output channels.

        Args:
            variables (dict[str, list[dict]]): Dictionary containing input data
                variables keyed by variable name.

        Returns:
            dict[str, list[dict]]: Dictionary with selected wave subsets in the
                output variables.

        Note:
            If the command is invalid, it will be skipped and variables returned unchanged.
            If input variable doesn't exist, an error is logged and processing continues.
        """
        self.good = self.validate()

        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")

        for (
            name,
            channel,
            resultant,
            out_channel,
            waves,
            time,
            maximum,
            direction,
            consecutive,
            alright,
            minimum
        ) in zip(
            self.name,
            self.channel,
            self.resultant,
            self.out_channel,
            self.waves,
            self.time,
            self.maximum,
            self.direction,
            self.consecutive,
            self.alright,
            self.minimum
        ):
            new_people = []
            if name not in variables:
                self.print(
                    "error", f"the variable name {name} is not in {variables.keys()}"
                )
            for person_ in variables.get(name):
                person = copy_dict(person_)
                person = self.take(
                    person,
                    channel,
                    out_channel,
                    waves,
                    time,
                    maximum,
                    direction,
                    consecutive,
                    alright,
                    minimum,
                )
                new_people.append(person)
            variables[resultant] = new_people
        return variables

    def take(
        self,
        person,
        channel,
        out_channel,
        waves,
        time,
        maximum,
        direction,
        consecutive,
        alright,
        minimum,
    ):
        """
        Perform the take operation on a single person's data.

        Selects a subset of waves based on the specified criteria, searching
        in the given direction and applying consecutiveness requirements.

        Args:
            person (dict): Dictionary containing person's data channels.
            channel (str): Name of the input channel to select from.
            out_channel (str): Name of the output channel for selected waves.
            waves (int): Number of waves to select (0 if using time or maximum).
            time (str): Time duration to select (converted to samples).
            maximum (bool): Whether to select maximum available valid waves.
            direction (str): Search direction ("+" forward, "-" backward).
            consecutive (bool): Whether to require consecutive valid waves.
            alright (str): Name of the mask channel for valid wave filtering.

        Returns:
            dict: Updated person dictionary with selected waves in out_channel.

        Note:
            - If `waves > 0`, wave count takes priority over time
            - If `maximum=True`, selects all available valid waves
            - When `consecutive=True`, resets selection on invalid waves
            - Direction "-" reverses search order but maintains original order in output
        """
        self.print(
            "debug",
            f"{self.type} of {person['FILENAME']} - ",
            self.debug_data(
                channel_name=channel,
                out_channel=out_channel,
                n_waves=waves,
                time=time,
                maximum=maximum,
                minimum=minimum,
                direction=direction,
                is_consequative=consecutive,
                alright_mask=alright,
            ),
        )

        # Incase no alright has been made yet
        person[alright] = self.ensure_alright(person, channel, alright)
        indices = list(range(len(person[alright])))
        if direction == "-":
            indices = indices[::-1]

        # Waves takes priority
        wave_format = waves > 0
        time = time_from_string(time, person["FREQUENCY"])

        hit = False
        max_length = 0
        max_indicies = []
        current_length = 0
        current_indicies = []
        for i in indices:
            if person[alright][i] == 1:
                current_indicies.append(i)
                current_length += len(person[channel][i])
                if wave_format:
                    if len(current_indicies) >= waves:
                        hit = True
                        if not maximum:
                            break
                else:
                    if current_length >= time:
                        hit = True
                        if not maximum:
                            break
            else:
                if wave_format:
                    if len(current_indicies) > len(max_indicies):
                        max_indicies = current_indicies
                        max_length = current_length
                else:
                    if current_length > max_length:
                        max_indicies = current_indicies
                        max_length = current_length
                if consecutive:
                    current_length = 0
                    current_indicies = []
        if wave_format:
            if len(current_indicies) > len(max_indicies):
                max_indicies = current_indicies
                max_length = current_length
        else:
            if current_length > max_length:
                max_indicies = current_indicies
                max_length = current_length

        if not hit and not maximum:
            self.print(
                "warning",
                f"Not enough valid waves found. Maximum found was {max_length/person['FREQUENCY']}s and {len(max_indicies)} waves.",
            )
        self.print(
            "index",
            f"Found {max_length/person['FREQUENCY']}s and {len(max_indicies)} waves.",
        )

        if direction == "-":
            max_indicies = max_indicies[::-1]
        if hit or not minimum:
            person[out_channel] = [person[channel][i] for i in max_indicies]
        else:
            person[out_channel] = []
        return person

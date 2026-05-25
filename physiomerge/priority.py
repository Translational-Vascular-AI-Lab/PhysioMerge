"""
Priority Command Module

This module provides the Priority class for selecting data from multiple
channels based on a priority order when certain channels may be empty or missing.
"""

from common import Command, copy_dict, time_from_string


class Priority(Command):
    """
    A command class for selecting data from multiple channels based on priority order.

    This class extends the Command base class to provide functionality for selecting
    data from the first available non-empty channel in a prioritized list. If the
    highest priority channel is empty or missing, it falls back to the next channel
    in the list.

    Attributes:
        channels (list[str]): Ordered list of channel names to check for data.
        good (bool): Validation status of the command instance.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize a Priority command instance.

        Args:
            command (dict): Configuration dictionary containing:
                - channels (list[str]): Ordered list of channel names to check
                - Additional parameters inherited from Command base class:
                  name, resultant, out_channel
        """
        super().__init__(command)
        self.channels = command.get("channels", [])

        self.good = False

    def validate(self) -> bool:
        """
        Validate the Priority instance configuration.

        Performs validation including type checking, list validation, and
        ensures the channels list is not empty.

        Returns:
            bool: True if the instance is valid, False otherwise.
        """
        is_valid = True

        required_str = ["channels"]
        if not self.check_type_inner(required_str, [str]):
            is_valid = False

        if is_valid:
            self.string_upper(required_str)

        self.equal_size(["channels"])
        if not isinstance(self.channels, list):
            self.print("error", f"Channels should be a list of strings, we got {type(self.channels)}")
            is_valid = False

        if not self.channels:
            self.print("error", f"Channels cant be a empty list")
            is_valid = False

        self.equal_size(["name", "resultant", "out_channel"])

        if not super().validate() or not is_valid:
            self.print("error", f"{self.type} class is not valid")
            return False

        self.print("debug", f"{self.type} class is valid")
        return True

    def execute(self, variables: dict[str, list[dict]]) -> dict[str, list[dict]]:
        """
        Execute the Priority command on the provided variables.

        Iterates through all persons in the specified input variables, selecting
        data from the highest priority non-empty channel for each person.

        Args:
            variables (dict[str, list[dict]]): Dictionary containing input data
                variables keyed by variable name.

        Returns:
            dict[str, list[dict]]: Dictionary with prioritized data in the
                output variables.

        Note:
            If the command is invalid, it will be skipped and variables returned
            unchanged. If no channels contain data for a person, the output
            channel will be empty.
        """
        self.good = self.validate()

        if not self.good:
            self.print("error", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        for name, resultant, out_channel in zip(
            self.name,
            self.resultant,
            self.out_channel,
        ):
            new_people = []
            if name not in variables:
                self.print(
                    "crash", f"the variable name {name} is not in {variables.keys()}"
                )
            for person_ in variables.get(name):
                person = copy_dict(person_)
                person = self.priority(person, self.channels, out_channel)
                new_people.append(person)
            variables[resultant] = new_people
        return variables

    def priority(
        self,
        person: dict[str, any],
        channels: list[str],
        out_channel: str,
    ) -> dict[str, any]:
        """
        Select data from the highest priority non-empty channel for a person.

        Checks channels in the specified order and selects data from the first
        channel that exists in the person's data and contains non-empty data.

        Args:
            person (dict[str, any]): Dictionary containing person's data channels.
            channels (list[str]): Ordered list of channel names to check.
            out_channel (str): Name of the output channel for selected data.

        Returns:
            dict[str, any]: Updated person dictionary with selected data in
                out_channel.

        Note:
            - Channels are checked in the order provided in the list
            - A channel is considered "empty" if it contains an empty list `[]`
            - If no channels contain data, the output channel will be empty `[]`
            - A warning is logged if no data is selected for a person
        """
        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                channels=channels,
                out_channel=out_channel,
            ),
        )

        selected = []
        for channel in channels:
            if channel in person:
                if person[channel]:
                    self.print("index", f"Selected channel is '{channel}'")
                    selected = person[channel]
                    break
        if selected == []:
            self.print("index", f"Empty output")
        person[out_channel] = selected

        if not person[out_channel]:
            self.print("warning", f"No data selected for {person["FILENAME"]}")

        return person

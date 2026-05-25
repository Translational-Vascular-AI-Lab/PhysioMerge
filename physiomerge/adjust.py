import numpy as np
from scipy.stats import mode

from common import Command, copy_dict, find_indices, time_from_string


class Adjust(Command):
    """
    Adjust signals between variables based on changes in a reference variable.

    This class extends `Command` and allows for adjusting channels in
    physiological data arrays. It can validate commands, execute adjustments,
    and update variable data accordingly.

    Attributes
    ----------
    name2 : str
        Secondary variable name used for reference. Corresponds to the dataset
        containing the reference signal.
    comments : str or list of str
        List of comments or markers indicating where adjustments should be applied.
    change_channel : str
        Channel in the reference variable used to detect changes that affect
        the primary variable.
    good : bool
        Boolean flag indicating whether the command instance is valid.
    name : list of str
        Names of primary variables to adjust. Inherited from `Command`.
    resultant : list of str
        Names of variables where adjusted data will be stored. Inherited from `Command`.
    channel : list of str
        Names of channels in the primary variable to adjust. Inherited from `Command`.
    out_channel : list of str
        Names of channels in the primary variable to write adjusted data to. Inherited from `Command`.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize an Adjust command instance.

        Parameters
        ----------
        command : dict
            Dictionary containing configuration for the adjustment.
            Expected keys include:

            - "name2" : str
                Secondary variable name used as reference.
            - "comments" : str or list of str
                Event markers or comments indicating where adjustments should occur.
            - "change_channel" : str
                Channel in the reference variable to detect changes.
            - "name" : list of str
                Names of primary variables to adjust.
            - "resultant" : list of str
                Names of variables to store the adjusted data.
            - "channel" : list of str
                Channels in primary variable to adjust.
            - "out_channel" : list of str
                Channels in primary variable to write adjusted data to.

        Notes
        -----
        Any missing keys will default to empty strings or empty lists.
        """
        super().__init__(command)
        self.name2 = command.get("in_2", "")
        self.comments = command.get("comments", [])
        self.change_channel = command.get("in_channel_2", "")
        self.shift = command.get("shift", "0s")
        self.direction = command.get("direction", "+")

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validate the Adjust command instance.

        Ensures that required attributes are present, of correct types,
        and that array sizes match expectations.

        Returns
        -------
        bool
            True if the command is valid, False otherwise.
        """
        is_valid = True

        if not self.check_type_inner(["name2", "comments", "change_channel", "shift", "direction"], [str]):
            is_valid = False

        self.string_upper(["name2", "comments", "change_channel"])

        # Validate array sizes
        try:
            required_fields = [
                "name",
                "resultant",
                "channel",
                "name2",
                "out_channel",
                "change_channel",
                "shift",
                "direction"
            ]
            self.equal_size(required_fields)
            self.equal_size(["comments"])
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
        Execute the Adjust command on the provided variables.

        Parameters
        ----------
        variables : dict
            Dictionary where keys are variable names and values are lists of
            dictionaries representing individual data entries.
            Each data entry dictionary should contain:
            - "FILENAME": Unique identifier for the subject.
            - "DATA": np.ndarray with shape (n_samples, n_channels).
            - "COLUMNS": list of channel names corresponding to DATA columns.
            - "COMMENTS": list of event markers or comments.
            - "MARKERS": list of lists indicating column indices of markers.

        Returns
        -------
        dict
            Updated variables dictionary with adjustments applied.
        """
        self.good = self.validate()
        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")

        for name, name2, resultant, channel, name2, out_channel, change_channel, shift, direction in zip(
            self.name,
            self.name2,
            self.resultant,
            self.channel,
            self.name2,
            self.out_channel,
            self.change_channel,
            self.shift,
            self.direction
        ):
            new_people = []
            if name not in variables:
                self.print("error", f"Variable with name '{name}' not found")
                continue

            for person_ in variables.get(name):
                person = copy_dict(person_)
                found = False
                person2 = None
                for other_person in variables.get(name2, []):
                    if person["FILENAME"] == other_person["FILENAME"]:
                        found = True
                        person2 = other_person

                if not found:
                    self.print(
                        "warning",
                        f"Variable with person '{person['FILENAME']}' in '{name2}' was not found",
                    )
                else:
                    person = self.adjust_channel(
                        person,
                        person2,
                        channel,
                        out_channel,
                        self.comments,
                        change_channel,
                        shift,
                        direction
                    )
                new_people.append(person)
            variables[resultant] = new_people

        return variables

    def adjust_channel(
        self,
        person1: dict[str, any],
        person2: dict[str, any],
        channel: str,
        out_channel: str,
        comments: list[str],
        change_channel: str,
        shift: str,
        direction:str
    ) -> dict[str, any]:
        """
        Adjust a single person's channel data based on another reference person.

        Parameters
        ----------
        person1 : dict
            The primary person's data dictionary to modify.
        person2 : dict
            The reference person's data dictionary.
        channel : str
            Name of the input channel to copy data from in person2.
        out_channel : str
            Name of the output cFThannel to write adjusted data to in person1.
        comments : list of str
            Comments indicating where adjustments should be applied.
        change_channel : str
            Channel used to detect changes in the reference data.

        Returns
        -------
        dict
            Updated `person1` dictionary with adjustments applied.
        """
        self.print(
            "debug",
            f"{self.type} of {person1['FILENAME']} - ",
            self.debug_data(
                channel_name=channel,
                out_channel=out_channel,
                comments=comments,
                change_channel=change_channel,
                shift=shift,
                direction=direction,
            ),
        )

        # Find input channel column in person2
        try:
            column = find_indices(channel, person2["COLUMNS"])[0]
        except IndexError:
            self.print(
                "error",
                f"Could not find channel '{channel}' in '{person2['COLUMNS']}'",
            )
            return person1

        change_start_index = 0

        # Detect change index if change_channel is provided
        if change_channel:
            try:
                change_column_idx = find_indices(change_channel, person2["COLUMNS"])[0]
                change_data = person2["DATA"][:, change_column_idx]

                for i in range(1, len(change_data)):
                    if change_data[i] != change_data[0]:
                        self.print("index", f"Found a change at {i}, channel {change_channel} went from {change_data[0]} to {change_data[i]}")
                        change_start_index = i
                        break

                self.print(
                    "index",
                    f"Change detected at index {change_start_index} in channel '{change_channel}'",
                )
            except IndexError:
                self.print(
                    "debug",
                    f"Could not find change channel '{change_channel}' in '{person2['COLUMNS']}'",
                )

        # Convert shift to samples
        shift_samples = time_from_string(shift, person1["FREQUENCY"])
        self.print("debug", f"Shift converted to {shift_samples} samples from '{shift}'")

        # Find the last comment to use as reference
        last_comment_idx = None
        if comments:
            # Collect all comment indices
            all_indices = []
            for comment in comments:
                if not comment:
                    continue
                indices = find_indices(comment, person1["COMMENTS"])
                all_indices.extend(indices)
            
            if all_indices:
                last_comment_idx = max(all_indices)  # Use the last occurrence
                self.print("index", f"Last comment found at index {last_comment_idx}")
            else:
                self.print(
                    "warning", f"Could not find any of {comments} for {person1['FILENAME']}"
                )

        # Calculate data length from person2 (starting after change detection)
        data_length = person2["DATA"].shape[0] - change_start_index
        
        # Calculate start index based on direction and last comment
        if last_comment_idx is not None:
            if direction == "-":
                # For "-" direction: data should END at the last comment
                # start = comment - data_length + 1 + shift
                start_index = last_comment_idx - data_length + 1 + shift_samples
                self.print("index", 
                    f"Direction '-': Data from index {change_start_index} to end of person2 "
                    f"(length {data_length}) will END at comment {last_comment_idx}"
                )
            else:  # direction == "+" or default
                # Regular behavior: data should START at the last comment
                # Note: +1 to start after the comment line
                start_index = last_comment_idx + 1 + shift_samples
                self.print("index", 
                    f"Direction '+': Data from index {change_start_index} to end of person2 "
                    f"(length {data_length}) will START at comment {last_comment_idx} + 1"
                )
        else:
            # No valid comment found - use default positioning
            if direction == "-":
                # Default to ending at the end of person1's data
                start_index = person1["DATA"].shape[0] - data_length + shift_samples
                self.print("index", 
                    f"No comment found, direction '-': Defaulting to END at last sample, "
                    f"start index {start_index}"
                )
            else:
                # Default to starting at shift position
                start_index = shift_samples
                self.print("index", 
                    f"No comment found, direction '+': Defaulting to START at shift {shift_samples}"
                )

        # Ensure start_index is not negative and within bounds
        start_index = max(0, start_index-change_start_index)
        self.print("index", f"Final start index after bounds checking: {start_index}")
        if (start_index - change_start_index < 0):
            remove_length = abs(start_index - change_start_index)
            source_data = person2["DATA"][remove_length:, column]
        else:
            source_data = person2["DATA"][:, column]

            

        # Get the data from person2 starting after the change
        source_len = len(source_data)

        n_row = person1["DATA"].shape[0]
        out_channel_exists = out_channel in person1["COLUMNS"]

        # Create new column if needed
        if not out_channel_exists:
            self.print("debug", f"Creating new column '{out_channel}', with size {n_row}")
            empty_column = np.zeros((n_row, 1))
            person1["DATA"] = np.hstack((person1["DATA"], empty_column))
            person1["COLUMNS"].append(out_channel)

        out_column_idx = find_indices(out_channel, person1["COLUMNS"])[0]

        # Calculate how much data we can copy (don't exceed person1's array)
        available_space = n_row - start_index
        copy_length = min(source_len, available_space)
        
        self.print("debug", 
            f"Source data length: {source_len}, Available space: {available_space}, "
            f"Copy length: {copy_length}"
        )

        # Apply data
        if copy_length > 0:
            person1["DATA"][
                start_index : start_index + copy_length, out_column_idx
            ] = source_data[:copy_length]

            # Update markers
            for i in range(copy_length):
                source_idx = change_start_index + i
                if source_idx < len(person2["MARKERS"]) and column in person2["MARKERS"][source_idx]:
                    target_idx = start_index + i
                    if target_idx < len(person1["MARKERS"]):
                        if out_column_idx not in person1["MARKERS"][target_idx]:
                            person1["MARKERS"][target_idx].append(out_column_idx)

            self.print("debug", f"Successfully copied {copy_length} samples to column '{out_channel}'")
        else:
            self.print("warning", f"No data copied - copy length is {copy_length}")

        return person1
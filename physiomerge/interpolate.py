from scipy import interpolate
import numpy as np
import math

from common import Command, copy_dict, time_from_string


class Interpolate(Command):
    def __init__(self, command: dict) -> None:
        super().__init__(command)
        self.function = command.get("function", "")
        self.length = command.get("length", 0)
        self.frequency = command.get("frequency", 0)
        self.frequency_channel = command.get("in_frequency", "")

        self.good = False

    def validate(self) -> bool:
        """
        Validates the data to ensure its correct.

        :return:
            bool: Returns True if the class instance is valid, otherwise returns False.
        """
        is_valid = True
        required_str = ["function", "frequency_channel"]
        if not self.check_type_inner(required_str, [str]):
            is_valid = False

        required_int = ["length", "frequency"]
        if not self.check_type_inner(required_int, [int]):
            is_valid = False

        if is_valid:
            self.string_upper(["function", "frequency_channel"])

        self.equal_size(
            [
                "name",
                "channel",
                "resultant",
                "out_channel",
                "function",
                "length",
                "frequency",
                "frequency_channel",
            ]
        )

        # Validate format
        valid_formats = ["PCHIP"]
        if not self.is_in_array(self.function, valid_formats):
            is_valid = False

        if not super().validate() or not is_valid:
            self.print("error", f"{self.type} class is not valid")
            return False

        self.print("debug", f"{self.type} class is valid")
        return True

    def execute(self, variables: dict[str, list[dict]]) -> dict[str, list[dict]]:
        """
        Executes the command to process the given variables.

        :param variables: dict[str, list[dict]] A dictionary of variables containing a list of people information.

        :return:
            dict[str, list[dict]]: The processed variables dictionary.
        """
        self.good = self.validate()

        if not self.good:
            self.print("error", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        for (
            name,
            channel,
            resultant,
            out_channel,
            function,
            length,
            frequency,
            frequency_channel,
        ) in zip(
            self.name,
            self.channel,
            self.resultant,
            self.out_channel,
            self.function,
            self.length,
            self.frequency,
            self.frequency_channel,
        ):
            new_people = []

            for person_ in variables.get(name):
                person = copy_dict(person_)
                found_freq = 0
                if frequency_channel and frequency == 0:
                    found_freq = person["FREQUENCY"]
                    found = False
                    for other_person in variables.get(frequency_channel):
                        if person["FILENAME"] == other_person["FILENAME"]:
                            found = True
                            if frequency != other_person["FREQUENCY"]:
                                found_freq = other_person["FREQUENCY"]
                            else:
                                self.print(
                                    "debug",
                                    f"Frequency for {person["FILENAME"]} is not changed",
                                )
                            break
                    if not found:
                        self.print(
                            "warning",
                            f"Could not find duplicate for {person["FILENAME"]}",
                        )

                if function == "PCHIP":
                    if channel == "DATA":
                        person = self.PCHIP_DATA(
                            person,
                            out_channel,
                            frequency if found_freq == 0 else found_freq,
                        )
                    else:
                        person = self.PCHIP(
                            person,
                            channel,
                            out_channel,
                            length=length,
                            frequency=frequency if found_freq == 0 else found_freq,
                        )
                new_people.append(person)
            variables[resultant] = new_people
        return variables

    def forward_fill_nan(self, arr):
        arr = arr.copy()
        for col in range(arr.shape[1]):
            # Check if first value is finite, if not set it to 0
            if not np.isfinite(arr[0, col]):
                arr[0, col] = 0
                
            mask = ~np.isfinite(arr[:, col])  # True for NaN, inf, -inf
            if np.any(mask):
                # Find indices of finite values
                valid = ~mask
                indices = np.where(valid, np.arange(len(arr)), 0)
                # Forward fill using cumulative max index of valid values
                np.maximum.accumulate(indices, out=indices)
                arr[:, col] = arr[indices, col]
        return arr

    def PCHIP(
        self,
        person: dict[str, any],
        channel: str,
        out_channel: str,
        length=0,
        frequency=0,
    ) -> dict[str, any]:
        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                function="PCHIP",
                channel_name=channel,
                out_channel=out_channel,
                length=length,
            ),
        )

        new_data = []
        for i, row in enumerate(person[channel]):
            if frequency != 0:
                duration = 1 / person["FREQUENCY"] * (len(row) - 1)
                new_n_samples = int(duration * frequency) + 1
                x_new = np.linspace(0, 1, num=new_n_samples)
            else:
                x_new = np.linspace(0, 1, num=int(length))
            x = np.linspace(0, 1, num=int(len(row)))

            if len(x) < 2:
                new_data.append(x_new)
                continue
            if any(math.isinf(value) or math.isnan(value) for value in row):
                new_data.append(x_new)
                continue

            output = interpolate.PchipInterpolator(x, row)(x_new)
            new_data.append(output.tolist())
        person[out_channel] = [[float(item) for item in row] for row in new_data]

        return person

    def PCHIP_DATA(
        self, person: dict[str, any], out_channel: str, freq: int
    ) -> dict[str, any]:
        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                function="PCHIP",
                out_channel=out_channel,
                frequency=freq,
                original_freq = person["FREQUENCY"]
            ),
        )

        n_samples, n_signals = person["DATA"].shape
        duration = (n_samples - 1) / person["FREQUENCY"]

        original_time = np.linspace(0, duration, num=n_samples)
        new_n_samples = int(duration * freq) + 1
        new_time = np.linspace(0, duration, num=new_n_samples)

        # Then use appropriate solution
        #if np.isnan(person["DATA"]).any():
        person["DATA"] = self.forward_fill_nan(person["DATA"])

        # Interpolate each signal column
        try:
            resampled_data = np.column_stack(
                [
                    interpolate.PchipInterpolator(original_time, person["DATA"][:, i])(
                        new_time
                    )
                    for i in range(n_signals)
                ]
            )
            person[out_channel] = resampled_data
        except ValueError as e:
            self.print(
                "error", f"data length {person["DATA"].shape}, new_time{new_time}, {e}"
            )
            self.print("error", f"Could not interpolate '{person["FILENAME"]}'")
            return person

        # I have to upsample markers here now
        original_length = len(person["MARKERS"])
        upsampled = [[] for _ in range(new_n_samples)]
        factor = (new_n_samples - 1) / (original_length - 1)

        for i, val in enumerate(person["MARKERS"]):
            new_index = int(round(i * factor))
            upsampled[new_index] = val
        person["MARKERS"] = upsampled


        # Upsampling or downsampling comments here
        old_comments = person["COMMENTS"]
        new_len = int(len(old_comments) * factor)

        # Avoid zero-length edge case
        if new_len <= 0:
            new_len = 1

        new_comments = [""] * new_len


        print(person["FILENAME"])
        for i, comm in enumerate(old_comments):
            if comm == "":
                continue

            # Scale index
            new_idx = int(round(i * factor))

            # Clamp to valid range
            new_idx = max(0, min(new_idx, new_len -1))

            try:
                new_comments[new_idx] = comm
            except IndexError:
                print("new index", new_index)
                print("comment error", comm)
                pass

        person["COMMENTS"] = new_comments
        person["FREQUENCY"] = freq



        return person


"""
class InterpolateChannel(Command):
    def __init__(self, command: dict) -> None:
        super().__init__(command)
        self.function = command.get("function", "")
        self.frequency_channel = command.get("name_frequency", "")
        self.frequency = command.get("frequency", 0)

        self.good = False

    def validate(self) -> bool:
        is_valid = True
        required_str = ["function", "frequency_channel"]
        if not self.check_type_inner(required_str, [str]):
            is_valid = False

        required_int = ["frequency"]
        if not self.check_type_inner(required_int, [int]):
            is_valid = False

        if is_valid:
            self.string_upper(["function", "frequency_channel"])

        self.equal_size(
            [
                "name",
                "channel",
                "frequency_channel",
                "resultant",
                "out_channel",
                "function",
            ]
        )

        for func in self.function:
            if func not in ["PCHIP"]:
                self.print("error", f"'{func}' is not a valid format for {self.type}")
                is_valid = False

        if not super().validate() or not is_valid:
            self.print("error", f"{self.type} class is not valid")
            return False

        self.print("debug", f"{self.type} class is valid")
        return True

    def execute(self, variables: dict[str, list[dict]]) -> dict[str, list[dict]]:
        self.good = self.validate()

        if not self.good:
            self.print("error", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        for (
            name,
            channel,
            resultant,
            out_channel,
            function,
            frequency_channel,
        ) in zip(
            self.name,
            self.channel,
            self.resultant,
            self.out_channel,
            self.function,
            self.frequency_channel,
        ):
            new_people = []
            for person_ in variables.get(name):
                person = copy_dict(person_)

                frequency = person["FREQUENCY"]
                if frequency_channel:
                    found = False
                    for other_person in variables.get(frequency_channel):
                        if person["FILENAME"] == other_person["FILENAME"]:
                            found = True
                            if frequency != other_person["FREQUENCY"]:
                                frequency == other_person["FREQUENCY"]
                                self.print(
                                    "debug",
                                    f"Frequency for {person["FILENAME"]} is being changed to {frequency}",
                                )
                            else:
                                self.print(
                                    "debug",
                                    f"Frequency for {person["FILENAME"]} is not changed",
                                )
                    if not found:
                        self.print(
                            "warning",
                            f"Could not find duplicate for {person["FILENAME"]}",
                        )
                if channel == "DATA":
                    person = self.PCHIP_DATA(person, out_channel, frequency)
                new_people.append(person)
            variables[resultant] = new_people
        return variables

    def PCHIP(
        self, person: dict[str, any], channel: str, out_channel: str, length: int
    ) -> dict[str, any]:
        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                function="PCHIP",
                channel_name=channel,
                out_channel=out_channel,
                length=length,
            ),
        )

        new_data = []
        x_new = np.linspace(0, 1, num=int(length))
        for i, row in enumerate(person[channel]):
            x = np.linspace(0, 1, num=int(len(row)))
            if len(x) < 2:
                new_data.append(x_new)
                continue
            if any(math.isinf(value) or math.isnan(value) for value in row):
                new_data.append(x_new)
                continue

            output = interpolate.PchipInterpolator(x, row)(x_new)
            new_data.append(output.tolist())
        person[out_channel] = [[float(item) for item in row] for row in new_data]

        return person

    def PCHIP_DATA(
        self, person: dict[str, any], out_channel: str, freq: int
    ) -> dict[str, any]:
        n_samples, n_signals = person["DATA"].shape
        duration = (n_samples - 1) / person["FREQUENCY"]

        original_time = np.linspace(0, duration, num=n_samples)
        new_n_samples = int(duration * freq) + 1
        new_time = np.linspace(0, duration, num=new_n_samples)

        if np.isnan(person["DATA"]).any():
            person["DATA"] = self.forward_fill_nan(person["DATA"])

        # Interpolate each signal column
        resampled_data = np.column_stack(
            [
                interpolate.PchipInterpolator(original_time, person["DATA"][:, i])(
                    new_time
                )
                for i in range(n_signals)
            ]
        )
        person["DATA"] = resampled_data

        # I have to upsample markers here now
        original_length = len(person["MARKERS"])
        upsampled = [[] for _ in range(new_n_samples)]
        factor = (new_n_samples - 1) / (original_length - 1)

        for i, val in enumerate(person["MARKERS"]):
            new_index = int(round(i * factor))
            upsampled[new_index] = val
        person["MARKERS"] = upsampled

        return person
"""

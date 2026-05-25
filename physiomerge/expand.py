# from bin.common import Command, copy_dict
import numpy as np
from scipy.stats import mode
from scipy import interpolate

from common import Command, copy_dict, time_from_string, find_indices


class Expand(Command):
    def __init__(self, command: dict) -> None:
        super().__init__(command)
        self.alright = command.get("alright", "")
        self.weights = command.get("weights", "")
        self.method = command.get("method", "flat")

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validates the Aggregate instance to ensure it meets the required criteria.
        """
        is_valid = True

        required_str = ["alright", "weights", "method"]
        if not self.check_type_inner(required_str, [str]):
            is_valid = False

        if is_valid:
            self.string_upper(["alright", "weights", "method"])

        # Validate method
        valid_methods = ["FLAT", "LINEAR", "NEAREST", "SLINEAR", "QUADRATIC", "CUBIC"]
        if not self.is_in_array(self.method, valid_methods):
            is_valid = False

        # ensure specified attributes have matching sizes
        try:
            self.equal_size(
                [
                    "name",
                    "resultant",
                    "channel",
                    "alright",
                    "out_channel",
                    "weights",
                    "method",
                ]
            )
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
        Executes the Aggregate command on the provided variables.
        """
        self.good = self.validate()
        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        for name, resultant, channel, out_channel, alright, weight, method in zip(
            self.name,
            self.resultant,
            self.channel,
            self.out_channel,
            self.alright,
            self.weights,
            self.method,
        ):
            new_people = []
            for person_ in variables.get(name, []):
                person = copy_dict(person_)
                person = self.expand2(
                    person, channel, out_channel, alright, weight, method
                )
                new_people.append(person)
            variables[resultant] = new_people

        return variables

    def expand(
        self,
        person: dict[str, any],
        channel: str,
        out_channel: str,
        alright: str,
        weight: str,
    ) -> dict[str, any]:

        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                channale_name=channel,
                out_channel=out_channel,
                alright_mask=alright,
                weight=weight,
            ),
        )

        # Filter the data using 'alright' mask
        if channel not in person.keys():
            self.print(
                "debug", f"Person does not contain '{channel}' in their {person.keys()}"
            )
            return person

        if not person[channel]:
            self.print("warning", f"Empty channel for {person['FILENAME']}")

        person[alright] = self.ensure_alright(person, channel, alright)
        person_weights = self.ensure_channel(person, channel, weight)

        output = []
        for val, val_alright, val_weight in zip(
            person[channel], person[alright], person_weights
        ):
            weighted = int(val_weight[0] * person["FREQUENCY"])
            new_val = float(val[0])
            if val_alright == 1:
                output.extend([new_val] * weighted)
            else:
                output.extend([0] * weighted)

        try:
            col = find_indices(out_channel, person["COLUMNS"])[0]
        except IndexError:
            self.print(
                "debug",
                f"Making new column for '{out_channel}' in '{person["FILENAME"]}'",
            )
            new_column = np.zeros((person["DATA"].shape[0], 1))
            person["DATA"] = np.hstack((person["DATA"], new_column))
            person["COLUMNS"].append(out_channel)
            col = find_indices(out_channel, person["COLUMNS"])[0]

        if col >= person["DATA"].shape[1]:
            new_column = np.zeros((person["DATA"].shape[0], 1))
            person["DATA"] = np.hstack((person["DATA"], new_column))

        # Pad or trunc
        if len(output) < person["DATA"].shape[0]:
            padding_length = person["DATA"].shape[0] - len(output)
            self.print("index", f"padded by {padding_length}")
            output.extend([output[-1]] * padding_length)
        # elif len(output) > person["DATA"].shape[0]:
        # output = output[: person["DATA"].shape[0]]
        output = np.array(output).reshape(-1, 1)

        person["DATA"][:, col] = output.flatten()
        # Append the result back to the person
        return person

    def expand2(
        self,
        person: dict[str, any],
        channel: str,
        out_channel: str,
        alright: str,
        weight: str,
        method: str,
    ):
        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                channale_name=channel,
                out_channel=out_channel,
                alright_mask=alright,
                weight=weight,
            ),
        )

        # Filter the data using 'alright' mask
        if channel not in person.keys():
            self.print(
                "debug", f"Person does not contain '{channel}' in their {person.keys()}"
            )
            return person

        if not person[channel]:
            self.print("warning", f"Empty channel for {person['FILENAME']}")

        person[alright] = self.ensure_alright(person, channel, alright)
        person_weights = self.ensure_channel(person, channel, weight)

        output = []
        for val, val_alright, val_weight in zip(
            person[channel], person[alright], person_weights
        ):
            weighted = int(val_weight[0] * person["FREQUENCY"])
            new_val = float(val[0])

            if val_alright == 1:
                output.extend([new_val] * weighted)
            else:
                output.extend([0] * weighted)

        if method != "FLAT":
            self.print("debug", f"using {method} method")

            target_length = len(output)

            x_original = np.arange(target_length)
            y_original = np.array(output)

            if len(output) >= 4:

                # Create a finer grid for interpolation, then sample back to original points
                x_fine = np.linspace(0, target_length - 1, target_length * 10)

                interp_func = interpolate.interp1d(
                    x_original,
                    y_original,
                    kind=method.lower(),
                    bounds_error=False,
                    fill_value=(y_original[0], y_original[-1]),
                )

                # Interpolate to finer grid
                y_fine = interp_func(x_fine)

                # Sample back to original grid (this will smooth the data)
                interp_func_fine = interpolate.interp1d(
                    x_fine,
                    y_fine,
                    kind=method.lower(),
                    bounds_error=False,
                    fill_value=(y_fine[0], y_fine[-1]),
                )
                interpolated_values = interp_func_fine(x_original)
                output = interpolated_values.tolist()
            else:
                self.print(
                    "error",
                    f"Person {person["FILENAME"]} does not more than 4 points in their expansion therefore, FLAT method is used",
                )
        else:
            self.print("debug", "using flat method")
        try:
            col = find_indices(out_channel, person["COLUMNS"])[0]
        except IndexError:
            self.print(
                "debug",
                f"Making new column for '{out_channel}' in '{person["FILENAME"]}'",
            )
            new_column = np.zeros((person["DATA"].shape[0], 1))
            person["DATA"] = np.hstack((person["DATA"], new_column))
            person["COLUMNS"].append(out_channel)
            col = find_indices(out_channel, person["COLUMNS"])[0]

        if col >= person["DATA"].shape[1]:
            new_column = np.zeros((person["DATA"].shape[0], 1))
            person["DATA"] = np.hstack((person["DATA"], new_column))

        # Pad or trunc
        if len(output) < person["DATA"].shape[0]:
            padding_length = person["DATA"].shape[0] - len(output)
            self.print("index", f"padded by {padding_length}")
            output.extend([output[-1]] * padding_length)
        # elif len(output) > person["DATA"].shape[0]:
        # output = output[: person["DATA"].shape[0]]
        output = np.array(output).reshape(-1, 1)

        person["DATA"][:, col] = output.flatten()

        return person

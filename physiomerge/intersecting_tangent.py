import numpy as np

from common import Command, copy_dict, time_from_string, find_indices


class IntersectingTangent(Command):
    def __init__(self, command: dict) -> None:
        super().__init__(command)
        self.max_index = command.get("max_index", "")
        self.min_index = command.get("min_index", "")

        self.good = self.validate()

    def validate(self) -> bool:
        is_valid = True

        required_str = ["max_index", "min_index"]
        if not self.check_type_inner(required_str, [str]):
            is_valid = False

        if is_valid:
            self.string_upper(["max_index", "min_index"])

        try:
            self.equal_size(
                [
                    "name",
                    "resultant",
                    "channel",
                    "max_index",
                    "min_index",
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
        Executes the Measurement command on the provided variables.
        """
        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")

        for name, resultant, channel, max_index, min_index in zip(
            self.name,
            self.resultant,
            self.channel,
            self.max_index,
            self.min_index,
        ):
            new_people = []
            # Safely get the list of people
            for person_ in variables.get(name):
                person = copy_dict(person_)
                person = self.int_tan(person, channel, max_index, min_index)
                new_people.append(person)
            variables[resultant] = new_people

        return variables

    def int_tan(self, person, channel, max_index, min_index):
        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                channel_name=channel,
                max_index=max_index,
                min_index=min_index,
            ),
        )

        try:
            column = find_indices(channel, person["COLUMNS"])[0]
        except IndexError:
            self.print(
                "error",
                f"Could not find column '{channel}' in '{person["COLUMNS"]}', no intersecting tangent for this person",
            )
            return person

        max_mark_col = find_indices(max_index, person["COLUMNS"])
        min_mark_col = find_indices(min_index, person["COLUMNS"])
        if not max_mark_col or not min_mark_col:
            self.print(
                "error",
                f"could not find a column {max_mark_col} or {min_mark_col} in {person["COLUMNS"]}, no intersecting tangent for this person",
            )
            return person

        max_mark = max_mark_col[0]
        min_mark = min_mark_col[0]

        wave = []
        min_val = None
        min_idx = None
        markers = person["MARKERS"]
        data_col = person["DATA"][:, column]

        for i, marker_row in enumerate(markers):
            # start a new segment when we hit the min marker
            if min_mark in marker_row:
                min_idx = i
                wave = [float(data_col[i])]  # start with current sample

            # if we're inside a segment (min found), append current sample
            elif min_idx is not None:
                wave.append(float(data_col[i]))

            # if we've reached max marker and we have an active segment, compute IT
            if (max_mark in marker_row) and (min_idx is not None):
                # ensure we have at least a few points to compute derivative
                if len(wave) < 3:
                    # not enough points; skip and reset
                    min_idx = None
                    wave = []
                    continue

                wavenp = np.array(wave, dtype=float)
                derivative = np.gradient(wavenp)
                max_slope_idx = int(np.argmax(derivative))
                max_slope = float(derivative[max_slope_idx])

                # tangent should pass through the point of max slope
                x0 = max_slope_idx
                y0 = wavenp[max_slope_idx]

                x_seg = np.arange(len(wavenp))
                tangent_line = max_slope * (x_seg - x0) + y0

                # horizontal line at the segment's minimum value
                min_seg_idx = int(np.argmin(wavenp))
                min_seg_val = float(wavenp[min_seg_idx])

                # find the index along the segment where tangent is closest to min value
                intersection_rel_idx = int(
                    np.argmin(np.abs(tangent_line - min_seg_val))
                )

                # convert to global index: wave[0] corresponds to min_idx
                intersection_global_idx = min_idx + intersection_rel_idx

                # safety: ensure MARKERS list has that index and it's a list
                if intersection_global_idx < 0 or intersection_global_idx >= len(
                    person["MARKERS"]
                ):
                    self.print(
                        "error",
                        f"Computed intersection index {intersection_global_idx} out of range, skipping",
                    )
                else:
                    if person["MARKERS"][intersection_global_idx] is None:
                        person["MARKERS"][intersection_global_idx] = []
                    # ensure it's a list
                    if not isinstance(person["MARKERS"][intersection_global_idx], list):
                        # replace or coerce
                        person["MARKERS"][intersection_global_idx] = [
                            person["MARKERS"][intersection_global_idx]
                        ]
                    person["MARKERS"][intersection_global_idx].append(column)

                # reset after handling the current segment
                min_idx = None
                wave = []
                wave.append(person["DATA"][i, column])
        return person

"""
Cut Command Module

This module provides the Cut class for extracting or removing specific segments
from data based on comments, time intervals, or markers.
"""

from common import Command, time_from_string, copy_dict, find_indices
import numpy as np


class Cut(Command):
    """
    A command class for extracting or removing data segments.

    This class extends the Command base class to provide functionality for
    cutting data based on comment markers or time intervals. It can extract
    segments between specified comments/markers or within defined time windows,
    with options to keep or remove the specified segments.

    Attributes:
        comment1 (str | list): Starting comment(s) for comment-based cutting.
        comment2 (str | list): Ending comment(s) for comment-based cutting.
        reset (bool): Whether to respect "RESET" comments as boundaries.
        period (str | list): Time period for time-based cutting.
        start (str | list): Start time for time-based cutting.
        direction (str | list): Direction for time cutting ("+" forward, "-" backward).
        boundary (str): Boundary handling: "outside" (remove segment) or "" (keep segment).
        form (str | list): Cutting form: "COMMENT" or "TIME".
        good (bool): Validation status of the command instance.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize a Cut command instance.

        Args:
            command (dict): Configuration dictionary containing:
                - comment1 (str|list): Starting comment(s) for comment cutting
                - comment2 (str|list): Ending comment(s) for comment cutting
                - reset (bool): Respect "RESET" comments as boundaries
                - period (str|list): Time period for time cutting
                - start (str|list): Start time for time cutting
                - direction (str|list): Time cutting direction ("+" or "-")
                - boundary (str): Boundary handling ("outside" or "")
                - form (str|list): Cutting form ("COMMENT" or "TIME")
                - Additional parameters inherited from Command base class
        """
        super().__init__(command)
        self.comment1 = command.get("comment1", "")
        self.comment2 = command.get("comment2", "")
        self.reset = command.get("reset", False)
        self.period = command.get("period", "")
        self.start = command.get("start", "")
        self.direction = command.get("direction", "+")
        self.boundary = command.get("boundary", "")
        self.form = command.get("form", "")

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validate the Cut instance configuration.

        Performs comprehensive validation including comment processing,
        form-specific validation, and parameter consistency checks.

        Returns:
            bool: True if the instance is valid, False otherwise.
        """
        is_valid = True

        # Ensure sizes match for comment-related attributes
        self.equal_size(["comment1"])
        self.equal_size(["comment2"])

        for i, comment in enumerate(self.comment1):
            self.comment1[i] = comment.replace(" ", "").strip("(){}").upper()
        for i, comment in enumerate(self.comment2):
            self.comment2[i] = comment.replace(" ", "").strip("(){}").upper()

        # Validate form-specific attribute sizes
        if is_valid:
            self.string_upper(["form"])
        if self.form == "COMMENT":
            try:
                self.equal_size(["name", "resultant"])
            except ValueError as e:
                self.print("error", f"Validation failed: {e}")
                is_valid = False
        elif self.form == "TIME":
            try:
                self.equal_size(["name", "resultant", "period", "start", "direction"])
            except ValueError as e:
                self.print("error", f"Validation failed: {e}")
                is_valid = False
        else:
            self.print("error", f"Invalid form '{self.form}', command skipped")
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
        Execute the Cut command on the provided variables.

        Routes execution to the appropriate method based on the cutting form.

        Args:
            variables (dict[str, list[dict[str, any]]]): Dictionary containing
                input data variables keyed by variable name.

        Returns:
            dict[str, list[dict[str, any]]]: Dictionary with cut/modified data
                in the output variables.

        Note:
            If the command is invalid, it will be skipped and variables returned
            unchanged.
        """
        self.good = self.validate()

        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command in form '{self.form}'")

        if self.form == "COMMENT":
            self.execute_comment(variables)
        elif self.form == "TIME":
            self.execute_time(variables)

        return variables

    def execute_comment(self, variables: dict[str, list[dict[str, any]]]) -> None:
        """
        Execute the 'comment' form of the Cut command.

        Processes all persons in the specified input variables using
        comment-based cutting.

        Args:
            variables (dict[str, list[dict[str, any]]]): Dictionary containing
                input data variables.
        """
        for name, resultant in zip(self.name, self.resultant):
            new_people = []
            if name not in variables:
                self.print(
                    "error", f"the variable name {name} is not in {variables.keys()}"
                )
            for person_ in variables.get(name):
                person = copy_dict(person_)
                person = self.split_comment(person)
                new_people.append(person)
            variables[resultant] = new_people

    def execute_time(self, variables: dict[str, list[dict[str, any]]]) -> None:
        """
        Execute the 'time' form of the Cut command.

        Processes all persons in the specified input variables using
        time-based cutting.

        Args:
            variables (dict[str, list[dict[str, any]]]): Dictionary containing
                input data variables.
        """
        for name, resultant, period, start, direction in zip(
            self.name, self.resultant, self.period, self.start, self.direction
        ):
            new_people = []
            if name not in variables:
                self.print(
                    "error", f"the variable name {name} is not in {variables.keys()}"
                )
            for person_ in variables.get(name):
                person = copy_dict(person_)
                person = self.split_time(
                    person,
                    time_from_string(period, person["FREQUENCY"]),
                    time_from_string(start, person["FREQUENCY"]),
                    direction,
                )
                new_people.append(person)
            variables[resultant] = new_people

    def split_comment(self, person: dict[str, any]) -> dict[str, any]:
        """
        Split the person's data based on comments.

        Finds segments between specified starting and ending comments,
        with optional respect for "RESET" comments.

        Args:
            person (dict[str, any]): Dictionary containing person's data.

        Returns:
            dict[str, any]: Updated person dictionary with data cut based on
                comments.

        Note:
            - comment1: Last occurrence used as start boundary
            - comment2: First occurrence used as end boundary
            - "*" in comment2: Matches any non-empty comment
            - RESET comments respected if reset=True
            - If comments not found, uses beginning/end of data as boundaries
        """
        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                comment1=self.comment1,
                comment2=self.comment2,
                reset=self.reset,
                boundary=self.boundary,
            ),
        )

        max_comments = len(person["COMMENTS"])
        c1_index = 0

        # Find the last occurrence of comment1
        found = False
        if self.comment1:
            for comment in self.comment1:
                indices = find_indices(comment, person["COMMENTS"])
                if indices:
                    c1_index = max(c1_index, indices[-1])
                    found = True
                self.print("index", f"c1 index selected as '{c1_index}'")
            if not found:
                self.print(
                    "error", f"Could not find {self.comment1} for {person["FILENAME"]}"
                )
                c1_index = 0

        ncomment = person["COMMENTS"][c1_index:] if c1_index else person["COMMENTS"]

        c2_index = max_comments
        reset_index = max_comments

        found = False
        # Find the first occurrence of "RESET" if `self.reset` is True
        if self.reset:
            reset_indices = find_indices("RESET", ncomment)
            if reset_indices:
                reset_index = c1_index + reset_indices[0]
                found = True
            self.print("index", f"reset index found as '{reset_index}'")

        # Find the first occurrence of any comment in `self.comment2`
        for comment in self.comment2:
            if comment == "*":
                for i, select in enumerate(person["COMMENTS"][c1_index + 1 :]):
                    if select:
                        c2_index = min(c2_index, c1_index + 1 + i)
                        found = True
            else:
                indices = find_indices(comment, ncomment)
                if indices:
                    c2_index = min(c2_index, c1_index + indices[0])
                    found = True
            self.print("index", f"c2 index found as '{c2_index}' for comment {comment}")
        if not found:
            self.print(
                "warning", f"Could not find {self.comment2} for {person["FILENAME"]}"
            )
            c2_index = max_comments

        c2_index = min(c2_index, reset_index)
        self.print("index", f"final c2 index selected as '{c2_index}'")

        self.print("debug", f"cutting data between '{c1_index}' '{c2_index}'")
        return self.cut_data(person, c1_index, c2_index)

    def split_time(
        self, person: dict[str, any], period: int, start: int, direction: str
    ) -> dict[str, any]:
        """
        Split the person's data based on time.

        Extracts or removes a time segment defined by start time and period.

        Args:
            person (dict[str, any]): Dictionary containing person's data.
            period (int): Time period in samples.
            start (int): Start time in samples.
            direction (str): Direction: "+" forward from start, "-" backward from end.

        Returns:
            dict[str, any]: Updated person dictionary with data cut based on time.

        Note:
            - direction="+": Segment from start to start+period
            - direction="-": Segment from (end-start-period) to (end-start)
            - Automatically clamps to valid data bounds
        """
        self.print(
            "debug",
            f"Cut by time: direction='{direction}', start='{start}', period='{period}', boundary='{self.boundary}'",
        )
        max_length = person["DATA"].shape[0]
        l1, l2 = (
            (start, start + period)
            if direction == "+"
            else (max_length - start - period, max_length - start)
        )
        l1, l2 = max(0, l1), min(max_length, l2)

        if l1 > l2:
            self.print("warning", f"Invalid indices: l1={l1}, l2={l2}. Command skipped.")
            return self.cut_data(person, l2, l2)

        return self.cut_data(person, l1, l2)

    def cut_data(self, person: dict[str, any], l1: int, l2: int) -> dict[str, any]:
        """
        Cut data, comments, and markers based on indices and boundary rules.

        Args:
            person (dict[str, any]): Dictionary containing person's data.
            l1 (int): Start index (inclusive).
            l2 (int): End index (exclusive).

        Returns:
            dict[str, any]: Updated person dictionary with data cut.

        Note:
            - boundary="outside": Removes segment between l1 and l2
            - boundary="": Keeps segment between l1 and l2
            - Cuts DATA (numpy array), COMMENTS (list), and MARKERS (list)
            - Handles numpy arrays and lists appropriately
        """
        for var in ["DATA", "COMMENTS", "MARKERS"]:
            if self.boundary == "outside":
                person[var] = (
                    np.concatenate((person[var][:l1, :], person[var][l2:, :]))
                    if var == "DATA"
                    else person[var][:l1] + person[var][l2:]
                )
                self.print("index", f"Removed indices {l1}-{l2} for {var}")
            else:
                person[var] = (
                    person[var][l1:l2, :] if var == "DATA" else person[var][l1:l2]
                )
                self.print("index", f"Kept indices {l1}-{l2} for {var}")
        return person

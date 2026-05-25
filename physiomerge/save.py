"""
save.py
=======

This module contains the `Save` class, which provides functionality to save structured
data from variables to files with configurable formatting, delimiters, headers, and
append/overwrite behavior.
"""

from common import Command, copy_dict
import re
import os
import numpy as np


class Save(Command):
    """
    Save command for writing structured variable data to files.

    Attributes
    ----------
    folder : str or list
        Folder path(s) where files should be saved.
    save_name : str or list
        Name(s) of output file(s).
    delim : str or list
        Delimiter(s) used to join list-type variables. Defaults to ",".
    format : str or list
        Format string(s) specifying the order and content of variables.
    header : str or list
        Header line(s) for the output file. Can be left blank.
    append : bool or list
        If True, append to existing file; if False, overwrite.
    good : bool
        Indicates whether this instance passed validation.
    """

    def __init__(self, command: dict) -> None:
        """
        Initializes the Save command with the provided configuration dictionary.

        Parameters
        ----------
        command : dict
            Dictionary containing keys:
            - folder
            - save_name
            - delim
            - format
            - header
            - append
        """
        super().__init__(command)
        self.folder = command.get("folder", "")
        self.save_name = command.get("save_name", "")
        self.delim = command.get("delim", ",")
        self.format = command.get("format", "")
        self.header = command.get("header", "")
        self.append = command.get("append", False)
        self.decimal = command.get("decimal", 2)

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validates the Save instance to ensure that required attributes have correct types
        and that list-type attributes are of equal length. Also validates the base class.

        Returns
        -------
        bool
            True if the instance is valid, False otherwise.
        """
        is_valid = True

        required_str = ["folder", "save_name", "format", "delim", "header"]
        if not self.check_type_inner(required_str, [str]):
            is_valid = False

        required_bool = ["append"]
        if not self.check_type_inner(required_bool, [bool]):
            is_valid = False

        required_int = ["decimal"]
        if not self.check_type_inner(required_int, [int]):
            is_valid = False

        if is_valid:
            self.string_upper(["format", "delim", "header"])

        try:
            self.equal_size(
                [
                    "name",
                    "append",
                    "folder",
                    "save_name",
                    "format",
                    "header",
                    "delim",
                    "decimal",
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
        Executes the Save command, writing data to files according to the format, header,
        and append options.

        Parameters
        ----------
        variables : dict
            Dictionary mapping variable names to lists of data entries.

        Returns
        -------
        dict
            The same variables dictionary, unchanged.
        """
        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        for name, append, folder, save_name, form, header, delim, decimal in zip(
            self.name,
            self.append,
            self.folder,
            self.save_name,
            self.format,
            self.header,
            self.delim,
            self.decimal,
        ):
            people = variables[name]
            save_data = ""

            if name not in variables:
                self.print(
                    "error", f"the variable name {name} is not in {variables.keys()}"
                )
            for person_ in variables.get(name):
                person = copy_dict(person_)
                save_data += self.make_save_data(person, form, delim, decimal)

            if header != "":
                save_data = header + "\n" + save_data
            save_data = save_data.replace("{NAME}", name)
            save_path = os.path.join(folder, save_name)
            self.print("debug", f"save path, '{save_path}'")

            if append:
                with open(save_path, "a") as f:
                    f.write(save_data)
            else:
                with open(save_path, "w") as f:
                    f.write(save_data)

        return variables

    def make_save_data(
        self, person: dict[str, any], form: str, delim, round_decimals
    ) -> str:
        """
        Generates a formatted string for a single data entry based on the specified format.
        Handles single values, lists, and lists of lists. Each inner list generates a separate line,
        with the fixed keys (e.g., PERSON, TIME) repeated.

        Parameters
        ----------
        person : dict
            Dictionary representing a single data entry.
        form : str
            Format string specifying the variables to include (e.g., "{PERSON}, {TIME}, {X}").
        round_decimals : int, optional
            Number of decimal places to round float/np.float64 values to (default is 2).

        Returns
        -------
        str
            Formatted string ready to be written to a file, with one line per inner list.
        """
        self.print(
            "debug",
            f"{self.type} of {person.get('FILENAME', 'unknown')} - ",
            self.debug_data(save_format=form),
        )

        form = form.upper()
        keys = re.findall(r"\{([^{}]+)\}", form)
        self.print("index", f"Total list of keys {keys}")

        single_values = {}  # For direct replacement
        multi_values = {}  # For multi-line replacement

        def format_number(val):
            """Convert numeric value to string with rounding."""
            if isinstance(val, (float, np.float64)):
                return str(round(float(val), round_decimals))
            return str(val)

        for key in keys:
            value = person.get(key)
            if value is None:
                self.print("index", f"Key '{key}' not found in {person.keys()}")
                continue

            # Handle single values
            if isinstance(value, (str, int, float, np.float64)):
                single_values[key] = format_number(value)
                self.print(
                    "index", f"Key '{key}' added with value '{single_values[key]}'"
                )
                continue

            # Handle lists
            if isinstance(value, list) or isinstance(value, np.ndarray):
                # Convert np.ndarray to list
                if isinstance(value, np.ndarray):
                    value = value.tolist()

                processed = []
                for item in value:
                    if isinstance(item, (list, np.ndarray)):
                        # Convert inner list/array items to string with rounding
                        if isinstance(item, np.ndarray):
                            item = item.tolist()
                        processed.append(delim.join(format_number(i) for i in item))
                    else:
                        processed.append(format_number(item))

                if len(processed) == 1:
                    single_values[key] = processed[0]
                    self.print(
                        "index", f"Key '{key}' added as single value '{processed[0]}'"
                    )
                else:
                    multi_values[key] = processed
                    self.print("index", f"Key '{key}' added as multi-line value")
                continue

        # Replace single values first
        for key, val in single_values.items():
            form = form.replace(f"{{{key}}}", val)

        # Handle multi-line replacement
        if multi_values:
            lines = []
            for row in zip(*multi_values.values()):
                line = form
                for key, val in zip(multi_values.keys(), row):
                    line = line.replace(f"{{{key}}}", val)
                lines.append(line)
            result = "\n".join(lines)
        else:
            result = form

        return result + "\n"

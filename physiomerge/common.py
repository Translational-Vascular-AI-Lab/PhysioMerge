"""
common
======

Shared utilities and base command infrastructure.

This module provides general-purpose helper functions and a base
``Command`` class used throughout the processing pipeline. The utilities
defined here are intentionally generic and reused across multiple stages
of physiological data processing.

Included functionality
----------------------
- List and dictionary utility helpers
- Safe copying of dictionaries containing NumPy arrays
- Parsing of human-readable time and frequency strings
- A standardized command abstraction with validation and verbosity control

Design notes
------------
- This module is dependency-light by design.
- NumPy is only required for safe copying of array-like values.
- Validation and logging utilities are centralized here to reduce
  duplication across command implementations.

This module is intended to be documented using Sphinx with ``autodoc``.
"""

from termcolor import colored
import numpy as np
import re
import logging
import os
from datetime import datetime


def find_indices(element, lst):
    """
    Return all index positions of a specified element in a list.

    This function iterates through the list and collects every index
    where the element matches the target value. It is useful when
    multiple occurrences of an item are expected.

    Parameters
    ----------
    element : any
        Element to search for in the list.
    lst : list
        List of elements in which to search.

    Returns
    -------
    list[int]
        A list of indices where the element occurs.
        Returns an empty list if the element is not present.
    """
    indices = []
    for i in range(len(lst)):
        if lst[i] == element:
            indices.append(i)
    return indices


def copy_dict(olddict):
    """
    Create a deep copy of a dictionary with NumPy-aware handling.

    Any NumPy arrays encountered are copied using ``ndarray.copy()``,
    ensuring that mutable numerical data are not shared between objects.
    Nested dictionaries are copied recursively.

    Parameters
    ----------
    olddict : dict
        Input dictionary which may contain NumPy arrays or nested dictionaries.

    Returns
    -------
    dict
        A deep copy of the input dictionary.
    """
    newdict = {}

    for key, value in olddict.items():
        if isinstance(value, np.ndarray):
            newdict[key] = value.copy()
        elif isinstance(value, dict):
            newdict[key] = copy_dict(value)
        else:
            newdict[key] = value

    return newdict


def time_from_string(time_str: str, sampling_freq: int) -> int:
    """
    Convert a time or frequency string into a number of samples.

    This function supports both time-based and frequency-based
    representations and converts them into sample counts using
    the provided sampling frequency.

    Supported formats
    -----------------
    Time units:
        - ``ns``   : nanoseconds
        - ``µs``   : microseconds
        - ``us``   : microseconds
        - ``ms``   : milliseconds
        - ``s``    : seconds
        - ``m``    : minutes
        - ``min``  : minutes
        - ``h``    : hours
        - ``hr``    : hours

    Frequency units:
        - ``Hz``   : Hertz
        - ``kHz``  : Kilohertz
        - ``MHz``  : Megahertz
        - ``BPM``  : Beats per minute

    Combined time units are supported (e.g., ``"1hr30min"``).

    Parameters
    ----------
    time_str : str
        Time or frequency string (e.g., ``"10Hz"``, ``"500ms"``,
        ``"1hr30min"``, ``"5BPM"``).
    sampling_freq : int
        Sampling frequency in Hz (samples per second).

    Returns
    -------
    int
        Equivalent number of samples.

    Raises
    ------
    ValueError
        If an unsupported unit is encountered.
    """
    UNIT_MULTIPLIERS = {
        "ns": 1e-9,
        "µs": 1e-6,
        "us": 1e-6,
        "ms": 1e-3,
        "s": 1,
        "m": 60,
        "min": 60,
        "h": 3600,
        "hr": 3600,
    }

    # Frequency-based parsing
    if time_str.endswith("kHz"):
        freq = float(re.match(r"[\d.]+", time_str).group()) * 1e3
        return int(sampling_freq / freq)
    elif time_str.endswith("MHz"):
        freq = float(re.match(r"[\d.]+", time_str).group()) * 1e6
        return int(sampling_freq / freq)
    elif time_str.endswith("BPM"):
        bpm = float(re.match(r"[\d.]+", time_str).group())
        return int(sampling_freq * (60 / bpm))
    elif time_str.endswith("Hz"):
        freq = float(re.match(r"[\d.]+", time_str).group())
        return int(sampling_freq / freq)

    # Time-based parsing
    total_seconds = 0.0
    matches = re.finditer(r"([\d.]+)([a-zA-Z]+)", time_str)

    for match in matches:
        value = float(match.group(1))
        unit = match.group(2)
        if unit in UNIT_MULTIPLIERS:
            total_seconds += value * UNIT_MULTIPLIERS[unit]
        else:
            raise ValueError(f"Unknown unit: {unit}")

    if not matches:
        # So here nothing else has happened, so just return the raw data
        return float(time_str)    
    

    return int(total_seconds * sampling_freq)


class Command:
    # Class-level logger shared across all instances
    session_logger = None
    log_file_path = None

    # Custom order and colors
    LOG_ORDER = [
        "none",
        "crash",
        "always",
        "error",
        "warning",
        "command",
        "debug",
        "index",
    ]
    LOG_COLOR = [
        "white",
        "red",
        "white",
        "red",
        "light_red",
        "cyan",
        "blue",
        "green",
        "white",
    ]

    # Map custom ranks to numeric levels
    LOG_LEVELS = {
        "crash": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "debug": logging.DEBUG,
        "command": 25,  # custom level
        "always": 26,  # custom level
        "index": 27,  # custom level
        "none": logging.NOTSET,
    }

    def __init__(self, command: dict) -> None:
        """
        Initialize a Command from a configuration dictionary.

        Parameters
        ----------
        command : dict
            Dictionary defining the command configuration.
        """
        self.type = command.get("class_name", "").upper()
        self.name = command.get("in", "")
        self.channel = command.get("in_channel", "")
        self.resultant = command.get("out", "")
        self.out_channel = command.get("out_channel", "")
        self.order = command.get("verbosity", "warning")

        # Initialize session logger
        if Command.session_logger is None:
            log_folder = "logs"
            os.makedirs(log_folder, exist_ok=True)

            # One log file per session
            time_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            Command.log_file_path = os.path.join(log_folder, f"{time_str}.log")

            # Create logger
            Command.session_logger = logging.getLogger("SESSION")
            Command.session_logger.setLevel(logging.DEBUG)

            # Add custom levels to logging module
            for name, level in Command.LOG_LEVELS.items():
                if not hasattr(logging, name.upper()):
                    logging.addLevelName(level, name.upper())

            # File handler
            fh = logging.FileHandler(Command.log_file_path)
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s: %(message)s", datefmt="%d/%m/%Y %H:%M:%S"
            )
            fh.setFormatter(formatter)
            Command.session_logger.addHandler(fh)

        self.logger = Command.session_logger
        self.good = False

    def __repr__(self) -> str:
        """
        Return a string representation of the Command instance.

        Includes all instance attributes for debugging and logging.
        """
        attributes = vars(self)
        items = ", ".join(f"{key}={repr(value)}" for key, value in attributes.items())
        return f"Command({items})"

    def validate(self) -> bool:
        """
        Validate required attributes and verbosity configuration.

        Returns
        -------
        bool
            True if the command is valid, False otherwise.
        """
        is_valid = True
        required_attributes = ["type", "name", "channel", "resultant", "out_channel"]
        if not self.check_type_inner(required_attributes, [str]):
            is_valid = False

        if is_valid:
            self.string_upper(required_attributes)

        if not isinstance(self.order, str):
            self.print(
                "error",
                f"verbosity order must be a string, instead got {type(self.order).__name__}",
            )
            is_valid = False

        if self.order not in ["index", "debug", "command", "warning", "error", "none"]:
            self.order = "command"

        # if no output make it the input name
        if self.resultant == [] or self.resultant == "":
            self.resultant = self.name

        # if no outut channel make it the input name
        if self.out_channel == [] or self.out_channel == "":
            self.out_channel = self.channel

        return is_valid

    def equal_size(self, variable_names: list[str]) -> None:
        """
        Ensure the specified attributes have the same length.

        Scalars are expanded to match the length of the longest list among variables.

        Parameters
        ----------
        variable_names : list of str
            Names of attributes to check and adjust.

        Raises
        ------
        AttributeError
            If any specified attribute does not exist.
        ValueError
            If list attributes have mismatched lengths.
        """
        variables = {name: getattr(self, name, None) for name in variable_names}

        # Ensure all variables exist
        for name in variable_names:
            if name not in variables:
                raise AttributeError(f"Variable '{name}' does not exist.")

        # Determine maximum size of lists
        max_size = max(
            (len(value) for value in variables.values() if isinstance(value, list)),
            default=1,
        )

        # Validate and adjust sizes
        for name, value in variables.items():
            if isinstance(value, list):
                if len(value) != max_size:
                    raise ValueError(
                        f"List '{name}' has a different size ({len(value)}) "
                        f"than the maximum size ({max_size})."
                    )
            else:
                # Expand scalar value to match maximum size
                setattr(self, name, [value] * max_size)

    def check_type_inner(
        self, attribute_names: list[str], acceptable_formats: list[type]
    ) -> bool:
        """
        Check that attributes match acceptable data types.

        Parameters
        ----------
        attribute_names : list of str
            Names of attributes to check.
        acceptable_formats : list of type
            Acceptable Python types.

        Returns
        -------
        bool
            True if all attributes conform to types, False otherwise.
        """
        for attr_name in attribute_names:
            value = getattr(self, attr_name)
            if value is None:
                self.print("error", f"Variable '{attr_name}' does not exist!")
                return False
            if not self.check_value_type(value, acceptable_formats):
                self.print(
                    "error",
                    f"Variable '{attr_name}' should be {acceptable_formats}, but got {type(value).__name__}.",
                )
                return False
        return True

    def check_value_type(self, value, acceptable_formats: list[type]) -> bool:
        """
        Check if a value matches any of the acceptable formats.

        Parameters
        ----------
        value : any
            Value to check.
        acceptable_formats : list of type
            Acceptable Python types.

        Returns
        -------
        bool
            True if value is valid, False otherwise.
        """
        if isinstance(value, list):
            return self.list_inner(value, acceptable_formats)
        return isinstance(value, tuple(acceptable_formats))

    def list_inner(self, list_var: list, acceptable_formats: list[type]) -> bool:
        """
        Recursively check nested lists for acceptable data types.

        Parameters
        ----------
        list_var : list
            Nested list to check.
        acceptable_formats : list of type
            Acceptable Python types.

        Returns
        -------
        bool
            True if all elements are valid, False otherwise.
        """
        for value in list_var:
            if isinstance(value, list):
                if not self.list_inner(value, acceptable_formats):
                    return False
            elif not isinstance(value, tuple(acceptable_formats)):
                return False
        return True

    def print(self, rank, *text):
        """
        Print a message with colored output based on rank.

        Parameters
        ----------
        rank : str
            Verbosity level of the message.
        text : tuple of str
            Additional text to display.

        Raises
        ------
        ValueError
            If rank is "crash", raises an exception.
        """
        rank = rank.lower()
        sel_order = self.order.lower() if self.order else "command"

        pos = self.find_index(rank, Command.LOG_ORDER)
        mini = self.find_index(sel_order, Command.LOG_ORDER)

        message = " ".join(str(t) for t in text)
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        full_message = f"[{timestamp}] {rank.upper()}: {message}"

        # Console output
        if pos <= mini and sel_order != "none":
            color_name = (
                Command.LOG_COLOR[pos] if pos < len(Command.LOG_COLOR) else "white"
            )
            print(colored(rank.upper(), color_name), message)

        # Logging using custom level
        level = Command.LOG_LEVELS.get(rank, logging.INFO)
        self.logger.log(level, full_message)

        # Raise exception for severe levels
        if rank in ["crash", "error"]:
            raise ValueError(message)

    @staticmethod
    def find_index(item, lst):
        try:
            return lst.index(item)
        except ValueError:
            return 0

    # ------------------------
    # Utility / Helper Methods
    # ------------------------

    def check_all(self, value, check):
        """
        Apply a check function to all elements if value is a list.
        """
        if isinstance(value, list):
            return all(check(x) for x in value)
        else:
            return check(value)

    def check_any(self, value, check):
        """
        Apply a check function to any element if value is a list.
        """
        if isinstance(value, list):
            return any(check(x) for x in value)
        else:
            return check(value)

    def debug_data(self, **variables) -> str:
        """
        Return a string representation of variables for debugging.

        Returns
        -------
        str
            Key-value pairs in the format "'key':'value', ..."
        """
        resultant = ""
        for name, value in variables.items():
            resultant += f"'{name}':'{value}', "
        return resultant.rstrip(", ")

    def string_upper(self, attribute_names: list[str]) -> None:
        """
        Convert string attributes (or lists of strings) to uppercase.

        Parameters
        ----------
        attribute_names : list of str
            Names of attributes to convert.
        """
        for attr_name in attribute_names:
            value = getattr(self, attr_name)
            if isinstance(value, str):
                setattr(self, attr_name, value.upper())
            elif isinstance(value, list):
                setattr(self, attr_name, [v.upper() for v in value])

    def ensure_alright(
        self, person: dict[str, any], channel: str, alright: str
    ) -> list:
        """
        Return a mask indicating valid entries for a channel.

        Parameters
        ----------
        person : dict
            Dictionary containing channel data.
        channel : str
            Channel key.
        alright : str
            Key for validity mask.

        Returns
        -------
        list[int]
            Binary mask (1=valid, 0=invalid).
        """
        alright_mask = []
        if alright:
            if alright not in person:
                self.print(
                    "debug",
                    "Alright cannot be found, a new alright is made with all valid",
                )
                channel_length = len(person[channel])
                alright_mask = [1 for _ in range(channel_length)]
            else:
                alright_mask = person[alright]
        else:
            self.print(
                "debug",
                "No alright provided, accepting all waves",
            )
            channel_length = len(person[channel])
            alright_mask = [1 for _ in range(channel_length)]
        return alright_mask

    def ensure_channel(
        self, person: dict[str, any], channel_base: str, channel_check: str
    ) -> list[list[int]]:
        """
        Ensure that a secondary channel exists and provide default weights.

        Parameters
        ----------
        person : dict
            Dictionary containing channel data.
        channel_base : str
            Base channel key.
        channel_check : str
            Secondary channel key to check.

        Returns
        -------
        list[list[int]]
            List of weights for each entry in the base channel.
        """
        channel_length = len(person[channel_base])

        if not channel_check:
            self.print(
                "debug",
                f"No Channel {channel_check} provided, blank weights made",
            )
            return [[1] for _ in range(channel_length)]

        if channel_check in person.keys():
            return person[channel_check]
        else:
            self.print("index", f"Only channels present are {person.keys()}")

        self.print(
            "warning",
            f"Channel {channel_check} cannot be found, a new alright is made with all valid",
        )
        return [[1] for _ in range(channel_length)]

    def is_in_array(self, val, array):
        """
        Check that val or all elements of val (if list) are in array.

        Parameters
        ----------
        val : str or list
            Value(s) to check.
        array : list
            List of supported options.

        Returns
        -------
        bool
            True if valid, False otherwise.
        """
        if isinstance(val, str) and val not in array:
            self.print(
                "error",
                f"Invalid form '{val}'. Supported forms are: {', '.join(array)}.",
            )
            return False

        if isinstance(val, list) and any(f not in array for f in val):
            invalid_formats = [f for f in val if f not in array]
            self.print(
                "error",
                f"Invalid formats {invalid_formats}. Supported formats are: {', '.join(array)}.",
            )
            return False

        return True

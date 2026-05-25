import tomllib
import argparse
from pathlib import Path

# Import all available commands
from adjust import Adjust
from aggregate import Aggregate
from arithmetic import Arithmetic
from check import Check
from cut import Cut
from delete import Delete
from expand import Expand
from filter import Filter
from find_wave import FindWave
from read import Read
from measurement import Measurement
from merge import Merge
from marker import Marker
from morphology import Morphology
from normalize import Normalize
from partition import Partition
from plot import Plot
from priority import Priority
from take import Take
from save import Save
from slice import Slice
from interpolate import Interpolate
from intersecting_tangent import IntersectingTangent


# ============================================================
# Unified Command Registry
# ============================================================
COMMANDS = {
    "adjust": Adjust,
    "aggregate": Aggregate,
    "arithmetic": Arithmetic,
    "check": Check,
    "cut": Cut,
    "delete":Delete,
    "expand": Expand,
    "filter": Filter,
    "peaks": FindWave,
    "interpolate": Interpolate,
    "marker": Marker,
    "measurement": Measurement,
    "merge": Merge,
    "morphology": Morphology,
    "normalize": Normalize,
    "partition": Partition,
    "plot": Plot,
    "priority": Priority,
    "read": Read,
    "save": Save,
    "slice": Slice,
    "take": Take,
    "inttan": IntersectingTangent,
}


# ============================================================
# MetaCommand Definition
# ============================================================
class MetaCommand:
    """Loads and executes a meta-command from metacommands/<meta_type>.toml."""

    def __init__(self, config: dict):
        self.meta_name = config["meta_name"]
        self.params = config
        self.order = config.get("verbosity", "command").lower()

        meta_file = Path("metacommands") / f"{self.meta_name}.toml"
        if not meta_file.exists():
            raise FileNotFoundError(f"Meta-command file not found: {meta_file}")

        with open(meta_file, "rb") as f:
            data = tomllib.load(f)

        self.commands = self._build_commands(data.get("command", []))

    def _replace_parameters(self, value):
        """Replace parameter placeholders with their actual values."""
        if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
            # Extract parameter name and return the actual value
            param_name = value[1:-1]  # Remove the braces
            return self.params.get(param_name, value)
        elif isinstance(value, list):
            # Recursively process each item in the list
            return [self._replace_parameters(item) for item in value]
        else:
            # Return numbers and other types as-is
            return value

    def _build_commands(self, command_list):
        commands = []
        for cmd_data in command_list:
            # Replace all parameter placeholders in the command data
            replaced_cmd_data = {}
            for k, v in cmd_data.items():
                replaced_cmd_data[k] = self._replace_parameters(v)

            # Handle the case where replacement resulted in multiple commands
            try:
                cmd_type = replaced_cmd_data["class_name"].lower()
            except KeyError as e:
                print(e)
                print(replaced_cmd_data)
                raise ValueError
            if cmd_type not in COMMANDS:
                raise ValueError(
                    f"Unknown command type '{cmd_type}' in meta-command '{self.meta_name}'"
                )

            # If any value became a list, create multiple commands
            list_fields = [
                k for k, v in replaced_cmd_data.items() if isinstance(v, list)
            ]
            if list_fields:
                # Find the maximum length to iterate through
                max_len = max(len(replaced_cmd_data[field]) for field in list_fields)

                for i in range(max_len):
                    single_cmd_data = {}
                    for k, v in replaced_cmd_data.items():
                        if isinstance(v, list):
                            # Use the i-th element, or cycle if shorter
                            single_cmd_data[k] = v[i % len(v)]
                        else:
                            single_cmd_data[k] = v
                    commands.append(COMMANDS[cmd_type](single_cmd_data))
            else:
                # Single command case
                commands.append(COMMANDS[cmd_type](replaced_cmd_data))

        return commands

    def execute(self, variables: dict):
        for cmd in self.commands:
            if self.order:
                cmd.order = self.order
            variables = cmd.execute(variables)
        return variables

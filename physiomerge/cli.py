import tomllib
import argparse
from pathlib import Path
from physiomerge import COMMANDS, MetaCommand


def process_files(files: list[str], order: str | None) -> None:
    """
    Run a list of TOML config files through the PhysioMerge command pipeline.

    Parameters
    ----------
    files : list[str]
        List of TOML files containing command specifications.
    order : str | None
        Verbosity/order level for command output.
    """
    variables = {}
    command_classes = COMMANDS | {"meta": MetaCommand}

    for file_path in map(Path, files):
        print(f"Running file '{file_path}'")
        with open(file_path, "rb") as f:
            data = tomllib.load(f)

        for command_data in data.get("command", []):
            cmd_type = command_data["class_name"].lower()
            cmd_class = command_classes.get(cmd_type)
            if not cmd_class:
                print(f"Warning: Unknown command type '{cmd_type}' in {file_path}")
                continue

            command = cmd_class(command_data)
            if order:
                command.order = order
            try:
                variables = command.execute(variables)
            except ValueError as e:
                print("ERROR", e)
                print("ERROR", command_data)
                raise ValueError


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run processing pipelines from TOML config files."
    )
    parser.add_argument("files", nargs="+", help="Configuration files to process")
    parser.add_argument(
        "-v",
        "--verbosity",
        choices=["index", "debug", "command", "warning", "error"],
        help="Increase output verbosity",
    )
    args = parser.parse_args()
    process_files(args.files, args.verbosity)

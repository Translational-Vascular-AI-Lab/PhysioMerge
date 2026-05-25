from common import Command


class Delete(Command):
    """
    Delete variables from the dataset.

    This command removes variables entirely from the variables dictionary.
    Its sole purpose is cleanup.
    """

    def __init__(self, command: dict) -> None:
        """
        Parameters
        ----------
        command : dict
            Expected keys:
            - "name" or "in": list[str]
                Names of variables to delete
        """
        super().__init__(command)
        self.good = self.validate()

    def validate(self) -> bool:
        is_valid = True
        self.string_upper(["name"])

        try:
            self.equal_size(
                ["name"]
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


    def execute(self, variables: dict) -> dict:
        """
        Updated variables dictionary with specified entries removed.
        """
        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")

        for name in self.name:
            if name in variables:
                self.print("debug", f"Deleting variable '{name}'")
                del variables[name]
            else:
                self.print("warning", f"Variable '{name}' not found, nothing to delete")

        return variables

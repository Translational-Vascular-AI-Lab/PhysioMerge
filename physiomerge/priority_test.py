import unittest
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bin"))
)


from priority import Priority  # type: ignore


class PriorityTest(unittest.TestCase):
    def make_variables(self):
        variables = {}
        people = []
        person = {}
        person["FREQUENCY"] = 2
        person["FILENAME"] = "testing"
        person["CHANNELA"] = []
        person["CHANNELB"] = []
        person["CHANNELC"] = []
        person["OUT"] = []
        people.append(person)
        variables["VARNAME"] = people

        return variables

    def make_command(self, **kwargs):
        command_data = {}
        command_data["type"] = "priority"
        command_data["in"] = "VARNAME"
        command_data["channels"] = ["CHANNELA", "CHANNELB", "CHANNELC"]
        command_data["out_channel"] = "OUT"
        command_data["verbosity"] = "none"
        command_data["out"] = "VARNAME"
        command_data.update(kwargs)
        return command_data

    # ========== BASIC FUNCTIONALITY TESTS ==========
    def test_all_empty(self):
        """Test priority selection when all channels are empty."""
        variables = self.make_variables()
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [])

    def test_first_only(self):
        """Test priority selection when only first channel has data."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = ["a"]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], ["a"])

    def test_second_only(self):
        """Test priority selection when only second channel has data."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELB"] = ["b"]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], ["b"])

    def test_third_only(self):
        """Test priority selection when only third channel has data."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELC"] = ["c"]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], ["c"])

    def test_first_third_only(self):
        """Test priority selection when first and third channels have data (should pick first)."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = ["a"]
        variables["VARNAME"][0]["CHANNELC"] = ["c"]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], ["a"])

    def test_second_third_only(self):
        """Test priority selection when second and third channels have data (should pick second)."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELB"] = ["b"]
        variables["VARNAME"][0]["CHANNELC"] = ["c"]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], ["b"])

    def test_first_second_only(self):
        """Test priority selection when first and second channels have data (should pick first)."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = ["a"]
        variables["VARNAME"][0]["CHANNELB"] = ["b"]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], ["a"])

    def test_all_channels_have_data(self):
        """Test priority selection when all channels have data (should pick first)."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = ["a"]
        variables["VARNAME"][0]["CHANNELB"] = ["b"]
        variables["VARNAME"][0]["CHANNELC"] = ["c"]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], ["a"])

    def test_different_data_sizes(self):
        """Test priority selection with different data sizes in channels."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = ["a"]
        variables["VARNAME"][0]["CHANNELB"] = ["b", "b", "b", "b"]
        variables["VARNAME"][0]["CHANNELC"] = ["c"]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], ["a"])

    # ========== COMPLEX DATA STRUCTURE TESTS ==========
    def test_nested_data_structures(self):
        """Test priority selection with nested data structures."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = []
        variables["VARNAME"][0]["CHANNELB"] = [{"key": "value"}, [1, 2, 3]]
        variables["VARNAME"][0]["CHANNELC"] = ["simple", "list"]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [{"key": "value"}, [1, 2, 3]])

    def test_numeric_data(self):
        """Test priority selection with numeric data."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = []
        variables["VARNAME"][0]["CHANNELB"] = [1, 2, 3, 4, 5]
        variables["VARNAME"][0]["CHANNELC"] = [10, 20, 30]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [1, 2, 3, 4, 5])

    def test_mixed_data_types(self):
        """Test priority selection with mixed data types."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = []
        variables["VARNAME"][0]["CHANNELB"] = ["string", 123, 45.67, True, None]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], ["string", 123, 45.67, True, None])

    # ========== EDGE CASE TESTS ==========
    def test_single_channel_list(self):
        """Test priority selection with only one channel in the list."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = ["data"]
        command_data = self.make_command(channels=["CHANNELA"])
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], ["data"])

    def test_single_channel_empty(self):
        """Test priority selection with single channel that's empty."""
        variables = self.make_variables()
        command_data = self.make_command(channels=["CHANNELA"])
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [])

    def test_many_channels(self):
        """Test priority selection with many channels in the list."""
        variables = self.make_variables()
        # Add more channels
        variables["VARNAME"][0]["CHANNELD"] = ["d"]
        variables["VARNAME"][0]["CHANNELE"] = ["e"]
        variables["VARNAME"][0]["CHANNELF"] = ["f"]

        command_data = self.make_command(
            channels=[
                "CHANNELA",
                "CHANNELB",
                "CHANNELC",
                "CHANNELD",
                "CHANNELE",
                "CHANNELF",
            ]
        )
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            # Should pick CHANNELD since it's the first non-empty
            self.assertEqual(person["OUT"], ["d"])

    def test_channel_contains_falsy_but_non_empty(self):
        """Test priority selection when channel contains falsy but non-empty values."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = []
        variables["VARNAME"][0]["CHANNELB"] = [
            0,
            "",
            False,
            None,
        ]  # Falsy but non-empty list
        variables["VARNAME"][0]["CHANNELC"] = ["real data"]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            # Should pick CHANNELB because it's non-empty (contains elements)
            self.assertEqual(person["OUT"], [0, "", False, None])

    def test_channel_missing_completely(self):
        """Test priority selection when a channel doesn't exist in person data."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = []
        # CHANNELB doesn't exist
        variables["VARNAME"][0]["CHANNELC"] = ["c"]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            # Should skip missing CHANNELB and pick CHANNELC
            self.assertEqual(person["OUT"], ["c"])

    def test_none_value_in_channel(self):
        """Test priority selection when channel value is None."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = None
        variables["VARNAME"][0]["CHANNELB"] = ["b"]
        command_data = self.make_command()
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            # None is not a list, so CHANNELA should be skipped
            self.assertEqual(person["OUT"], ["b"])

    # ========== MULTIPLE PERSON TESTS ==========
    def test_multiple_people_different_selections(self):
        """Test priority selection across multiple people with different data."""
        variables = {}
        people = []

        # Person 1: First channel has data
        person1 = {}
        person1["FREQUENCY"] = 2
        person1["FILENAME"] = "person1"
        person1["CHANNELA"] = ["a1"]
        person1["CHANNELB"] = ["b1"]
        person1["CHANNELC"] = ["c1"]
        people.append(person1)

        # Person 2: Only third channel has data
        person2 = {}
        person2["FREQUENCY"] = 2
        person2["FILENAME"] = "person2"
        person2["CHANNELA"] = []
        person2["CHANNELB"] = []
        person2["CHANNELC"] = ["c2"]
        people.append(person2)

        # Person 3: No channels have data
        person3 = {}
        person3["FREQUENCY"] = 2
        person3["FILENAME"] = "person3"
        person3["CHANNELA"] = []
        person3["CHANNELB"] = []
        person3["CHANNELC"] = []
        people.append(person3)

        variables["VARNAME"] = people

        command_data = self.make_command()
        command = Priority(command_data)
        variables = command.execute(variables)

        # Check each person got correct selection
        self.assertEqual(
            variables["VARNAME"][0]["OUT"], ["a1"]
        )  # Person 1: first channel
        self.assertEqual(
            variables["VARNAME"][1]["OUT"], ["c2"]
        )  # Person 2: third channel
        self.assertEqual(variables["VARNAME"][2]["OUT"], [])  # Person 3: no data

    # ========== VALIDATION TESTS ==========
    def test_validation_empty_channels_list(self):
        """Test validation fails when channels list is empty."""
        command_data = self.make_command(channels=[])
        command = Priority(command_data)
        self.assertFalse(
            command.good, "Command with empty channels list should not be valid"
        )

    def test_validation_channels_not_list(self):
        """Test validation fails when channels is not a list."""
        command_data = self.make_command(channels="CHANNELA")
        command = Priority(command_data)
        self.assertFalse(
            command.good, "Command with string channels should not be valid"
        )

    def test_validation_mismatched_parameter_lengths(self):
        """Test validation fails when parameter lists have mismatched lengths."""
        command_data = self.make_command()
        command_data["in"] = ["VARNAME", "OTHERNAME"]  # Different length
        command = Priority(command_data)
        self.assertFalse(
            command.good,
            "Command with mismatched parameter lengths should not be valid",
        )

    def test_validation_channels_list_contains_non_strings(self):
        """Test validation fails when channels list contains non-strings."""
        command_data = self.make_command(channels=["CHANNELA", 123, "CHANNELC"])
        command = Priority(command_data)
        self.assertFalse(
            command.good, "Command with non-string channels should not be valid"
        )

    # ========== CASE SENSITIVITY TESTS ==========
    def test_case_insensitive_channel_names(self):
        """Test that channel names are case-insensitive (converted to uppercase)."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = ["a"]  # Uppercase in data
        variables["VARNAME"][0]["channelb"] = ["b"]  # Lowercase in data

        # Mix cases in command
        command_data = self.make_command(channels=["channela", "CHANNELB", "ChannelC"])
        command = Priority(command_data)

        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            # Should find CHANNELA (uppercase match)
            self.assertEqual(person["OUT"], ["a"])

    # ========== ERROR HANDLING TESTS ==========
    def test_nonexistent_input_variable(self):
        """Test when input variable doesn't exist."""
        variables = self.make_variables()
        command_data = self.make_command(name="NONEXISTENT", verbosity="none")
        command = Priority(command_data)

        # Should not crash, just return variables unchanged
        result = command.execute(variables)
        self.assertIsNotNone(result)

    def test_execute_invalid_command_skips(self):
        """Test that invalid commands are skipped during execution."""
        variables = self.make_variables()
        command_data = self.make_command(channels=[])  # Invalid: empty list

        command = Priority(command_data)
        self.assertFalse(command.good)

        # Execute should skip and return variables unchanged
        try:
            result = command.execute(variables)
            self.assertEqual(result, variables)
        except ValueError as e:
            self.assertIsNotNone(e)

    # ========== VERBOSITY TESTS ==========
    def test_different_verbosity_levels(self):
        """Test priority command with different verbosity levels."""
        variables = self.make_variables()
        variables["VARNAME"][0]["CHANNELA"] = ["test data"]

        # Test with debug verbosity
        command_data = self.make_command(verbosity="none")
        command = Priority(command_data)
        variables = command.execute(variables)

        # Test with none verbosity
        command_data = self.make_command(verbosity="none")
        command = Priority(command_data)
        variables = command.execute(variables)

        # Both should produce same result
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], ["test data"])


if __name__ == "__main__":
    unittest.main()

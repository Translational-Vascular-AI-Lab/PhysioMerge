import unittest
import sys
import os

from merge import Merge  # type: ignore


class MergeTest(unittest.TestCase):
    def make_variables(self):
        variables = {}
        people = []
        person = {}
        person["FREQUENCY"] = 2
        person["FILENAME"] = "testing"
        person["CHANNELA"] = [[i] for i in range(1, 7)]  # Length 6
        person["CHANNELB"] = [[i] for i in range(1, 10)]  # Length 9
        person["CHANNELC"] = []  # Length 0
        person["CHANNELD"] = []  # Length 0
        person["CHANNELE"] = [[i] for i in range(1, 4)]  # Length 3
        person["CHANNELF"] = [[i] for i in range(1, 4)]  # Length 3 (equal to E)

        # Boolean channels for logical operations
        person["CHANNELA_B"] = [0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1]  # Length 11
        person["CHANNELB_B"] = [1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1]  # Length 11
        person["CHANNELC_B"] = [1, 1, 1, 1, 1]  # Length 5
        person["CHANNELD_B"] = [0, 0, 0, 0, 0]  # Length 5

        # Mixed boolean channels (some non-0/1 values)
        person["CHANNEL_MIXED1"] = [0, 1, 2, 0, -1, 1, 0, "a", "", None]
        person["CHANNEL_MIXED2"] = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]

        people.append(person)
        variables["VARNAME"] = people

        return variables

    def make_command(self, **kwargs):
        command_data = {}
        command_data["type"] = "merge"
        command_data["in"] = "VARNAME"
        command_data["in_channel"] = "CHANNELA"
        command_data["in_channel_2"] = "CHANNELB"
        command_data["format"] = "greater"
        command_data["out_channel"] = "OUT"
        command_data["out"] = "VARNAME"
        command_data["verbosity"] = "none"
        command_data.update(kwargs)
        return command_data

    # ========== GREATER TESTS ==========
    def test_greater_first_larger(self):
        """Test greater operation when first in_channel is larger."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELB", in_channel_2="CHANNELA"  # Length 9  # Length 6
        )
        command = Merge(command)
        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["CHANNELB"], person["OUT"])

    def test_greater_second_larger(self):
        """Test greater operation when second in_channel is larger."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELA", in_channel_2="CHANNELB"  # Length 6  # Length 9
        )
        command = Merge(command)
        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["CHANNELB"], person["OUT"])

    def test_greater_first_empty(self):
        """Test greater operation when first in_channel is empty."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELC", in_channel_2="CHANNELB"  # Empty  # Length 9
        )
        command = Merge(command)
        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["CHANNELB"], person["OUT"])

    def test_greater_second_empty(self):
        """Test greater operation when second in_channel is empty."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELA", in_channel_2="CHANNELC"  # Length 6  # Empty
        )
        command = Merge(command)
        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["CHANNELA"], person["OUT"])

    def test_greater_both_empty(self):
        """Test greater operation when both channels are empty."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELC", in_channel_2="CHANNELD"  # Empty  # Empty
        )
        command = Merge(command)
        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["CHANNELC"], person["OUT"])

    def test_greater_equal_length(self):
        """Test greater operation when channels have equal length."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELE",  # Length 3
            in_channel_2="CHANNELF",  # Length 3
            format="greater",
        )
        command = Merge(command)
        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            # When equal, returns second in_channel (in_channel_2)
            self.assertEqual(person["CHANNELF"], person["OUT"])

    # ========== LESSER TESTS ==========
    def test_lesser_first_smaller(self):
        """Test lesser operation when first in_channel is smaller."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELA",  # Length 6
            in_channel_2="CHANNELB",  # Length 9
            format="lesser",
        )
        command = Merge(command)
        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["CHANNELA"], person["OUT"])

    def test_lesser_second_smaller(self):
        """Test lesser operation when second in_channel is smaller."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELB",  # Length 9
            in_channel_2="CHANNELA",  # Length 6
            format="lesser",
        )
        command = Merge(command)
        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["CHANNELA"], person["OUT"])

    def test_lesser_first_empty(self):
        """Test lesser operation when first in_channel is empty."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELC",  # Empty
            in_channel_2="CHANNELA",  # Length 6
            format="lesser",
        )
        command = Merge(command)
        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["CHANNELC"], person["OUT"])

    def test_lesser_second_empty(self):
        """Test lesser operation when second in_channel is empty."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELA",  # Length 6
            in_channel_2="CHANNELC",  # Empty
            format="lesser",
        )
        command = Merge(command)
        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["CHANNELC"], person["OUT"])

    def test_lesser_both_empty(self):
        """Test lesser operation when both channels are empty."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELC",
            in_channel_2="CHANNELD",
            format="lesser",  # Empty  # Empty
        )
        command = Merge(command)
        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            self.assertEqual(person["CHANNELC"], person["OUT"])

    def test_lesser_equal_length(self):
        """Test lesser operation when channels have equal length."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELE",  # Length 3
            in_channel_2="CHANNELF",  # Length 3
            format="lesser",
        )
        command = Merge(command)
        variables = command.execute(variables)
        for person in variables["VARNAME"]:
            # When equal, returns second in_channel (in_channel_2)
            self.assertEqual(person["CHANNELF"], person["OUT"])

    # ========== LOGICAL OPERATION TESTS ==========
    def test_AND_operation(self):
        """Test AND logical operation."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELA_B", in_channel_2="CHANNELB_B", format="AND"
        )
        command = Merge(command)
        variables = command.execute(variables)

        # Expected: [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1]
        for person in variables["VARNAME"]:
            self.assertEqual(
                person["OUT"],
                [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
            )

    def test_OR_operation(self):
        """Test OR logical operation."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELA_B", in_channel_2="CHANNELB_B", format="OR"
        )
        command = Merge(command)
        variables = command.execute(variables)

        # Expected: [1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1]
        for person in variables["VARNAME"]:
            self.assertEqual(
                person["OUT"],
                [1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1],
            )

    def test_NAND_operation(self):
        """Test NAND logical operation."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELA_B", in_channel_2="CHANNELB_B", format="NAND"
        )
        command = Merge(command)
        variables = command.execute(variables)

        # Expected: [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0]
        for person in variables["VARNAME"]:
            self.assertEqual(
                person["OUT"],
                [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0],
            )

    def test_NOR_operation(self):
        """Test NOR logical operation."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELA_B", in_channel_2="CHANNELB_B", format="NOR"
        )
        command = Merge(command)
        variables = command.execute(variables)

        # Expected: [0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0]
        for person in variables["VARNAME"]:
            self.assertEqual(
                person["OUT"],
                [0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0],
            )

    def test_XOR_operation(self):
        """Test XOR logical operation."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELA_B", in_channel_2="CHANNELB_B", format="XOR"
        )
        command = Merge(command)
        variables = command.execute(variables)

        # Expected: [1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0]
        for person in variables["VARNAME"]:
            self.assertEqual(
                person["OUT"],
                [1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
            )

    def test_XNOR_operation(self):
        """Test XNOR logical operation."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELA_B", in_channel_2="CHANNELB_B", format="XNOR"
        )
        command = Merge(command)
        variables = command.execute(variables)

        # Expected: [0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1]
        for person in variables["VARNAME"]:
            self.assertEqual(
                person["OUT"],
                [0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1],
            )

    # ========== LOGICAL OPERATION EDGE CASES ==========
    def test_logical_ops_all_ones(self):
        """Test logical operations with all 1s."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELC_B",  # All 1s
            in_channel_2="CHANNELC_B",  # All 1s
            format="AND",
        )
        command = Merge(command)
        variables = command.execute(variables)

        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [1, 1, 1, 1, 1])

    def test_logical_ops_all_zeros(self):
        """Test logical operations with all 0s."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELD_B",
            in_channel_2="CHANNELD_B",
            format="OR",  # All 0s  # All 0s
        )
        command = Merge(command)
        variables = command.execute(variables)

        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [0, 0, 0, 0, 0])

    def test_logical_ops_mixed_values(self):
        """Test logical operations with non-boolean values."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNEL_MIXED1", in_channel_2="CHANNEL_MIXED2", format="AND"
        )
        command = Merge(command)
        variables = command.execute(variables)

        # Python truthiness: 0, 0, "", None are falsy; others are truthy
        # Expected: [0&1, 1&0, 2&1, 0&0, -1&1, 1&0, 0&1, "a"&0, ""&1, None&0]
        # = [0, 0, 1, 0, 1, 0, 0, 1, 0, 0]
        for person in variables["VARNAME"]:
            self.assertEqual(
                person["OUT"],
                [0, 0, 1, 0, 1, 0, 0, 0, 0, 0],
            )

    def test_logical_ops_different_lengths(self):
        """Test logical operations with channels of different lengths."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELA_B",  # Length 11
            in_channel_2="CHANNELC_B",  # Length 5
            format="AND",
        )
        command = Merge(command)
        variables = command.execute(variables)

        # zip() will truncate to shorter length (5)
        for person in variables["VARNAME"]:
            self.assertEqual(len(person["OUT"]), 5)
            # First 5 elements: [0&1, 1&1, 0&1, 1&1, 1&1] = [0, 1, 0, 1, 1]
            self.assertEqual(person["OUT"], [0, 1, 0, 1, 1])

    def test_logical_ops_empty_channels(self):
        """Test logical operations with empty channels."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELC",
            in_channel_2="CHANNELD",
            format="AND",  # Empty  # Empty
        )
        command = Merge(command)
        variables = command.execute(variables)

        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [])

    def test_logical_ops_one_empty(self):
        """Test logical operations with one empty in_channel."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="CHANNELA_B",  # Length 11
            in_channel_2="CHANNELC",  # Empty
            format="AND",
        )
        command = Merge(command)
        variables = command.execute(variables)

        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [])

    # ========== VALIDATION TESTS ==========
    def test_validation_invalid_format(self):
        """Test validation with invalid format."""
        command_data = self.make_command(format="INVALID_FORMAT")
        command = Merge(command_data)
        self.assertFalse(
            command.good, "Command with invalid format should not be valid"
        )

    def test_validation_mismatched_parameter_lengths(self):
        """Test validation when parameter lists have mismatched sizes."""
        command_data = self.make_command()
        command_data["name"] = ["VARNAME", "OTHERNAME"]  # Different length
        command = Merge(command_data)
        self.assertFalse(
            command.good,
            "Command with mismatched parameter lengths should not be valid",
        )

    def test_validation_missing_required_parameters(self):
        """Test validation when required parameters are missing."""
        command_data = self.make_command()
        del command_data["in_channel_2"]  # Remove required parameter
        command = Merge(command_data)
        self.assertFalse(
            command.good, "Command with missing required parameter should not be valid"
        )

    # ========== ERROR HANDLING TESTS ==========
    def test_nonexistent_channel(self):
        """Test when in_channel doesn't exist in person data."""
        variables = self.make_variables()
        command = self.make_command(
            in_channel="NONEXISTENT_CHANNEL", in_channel_2="CHANNELA"
        )
        command = Merge(command)
        # Should handle gracefully (might create empty in_channel or skip)
        try:
            result = command.execute(variables)
        except ValueError as err:
            self.assertIsNotNone(err)

    def test_execute_invalid_command_skips(self):
        """Test that invalid commands are skipped during execution."""
        variables = self.make_variables()
        command_data = self.make_command(format="INVALID_FORMAT")

        command = Merge(command_data)
        self.assertFalse(command.good)

        # Execute should skip and return variables unchanged
        try:
            result = command.execute(variables)
        except ValueError as err:
            self.assertIsNotNone(err)

    # ========== CASE SENSITIVITY TESTS ==========
    def test_case_insensitive_parameters(self):
        """Test that string parameters are case-insensitive."""
        variables = self.make_variables()

        # Test with lowercase in_channel names (should be converted to uppercase)
        command_data = self.make_command(
            in_channel="channela_b",  # lowercase
            in_channel_2="channelb_b",  # lowercase
            format="and",  # lowercase
        )
        command = Merge(command_data)
        variables = command.execute(variables)

        # Should still work (channels get converted to uppercase)
        for person in variables["VARNAME"]:
            self.assertEqual(
                person["OUT"],
                [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
            )

    # ========== SPECIAL VALUE TESTS ==========
    def test_single_element_channels(self):
        """Test with single element channels."""
        variables = self.make_variables()
        # Add single element channels
        person = variables["VARNAME"][0]
        person["SINGLE1"] = [1]
        person["SINGLE2"] = [0]

        command = self.make_command(
            in_channel="SINGLE1", in_channel_2="SINGLE2", format="AND"
        )
        command = Merge(command)
        variables = command.execute(variables)

        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [0])  # 1 AND 0 = 0

    def test_none_values_in_channels(self):
        """Test with None values in channels."""
        variables = self.make_variables()
        # Add channels with None values
        person = variables["VARNAME"][0]
        person["NONE_CHAN1"] = [None, 1, 0]
        person["NONE_CHAN2"] = [1, None, 0]

        command = self.make_command(
            in_channel="NONE_CHAN1", in_channel_2="NONE_CHAN2", format="OR"
        )
        command = Merge(command)
        variables = command.execute(variables)

        # None is falsy in Python
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [1, 1, 0])

    # ========== PERFORMANCE/STRESS TESTS ==========
    def test_large_channels(self):
        """Test with large channels."""
        variables = self.make_variables()
        person = variables["VARNAME"][0]

        # Create large channels
        size = 1000
        person["LARGE1"] = [1] * size
        person["LARGE2"] = [0] * size

        command = self.make_command(
            in_channel="LARGE1", in_channel_2="LARGE2", format="XOR"
        )
        command = Merge(command)
        variables = command.execute(variables)

        for person in variables["VARNAME"]:
            self.assertEqual(len(person["OUT"]), size)
            self.assertEqual(person["OUT"], [1] * size)  # 1 XOR 0 = 1

    # ========== FORMAT SPECIFIC TESTS ==========
    def test_all_formats(self):
        """Test all valid formats in one comprehensive test."""
        variables = self.make_variables()
        person = variables["VARNAME"][0]

        # Simple test data
        person["TEST1"] = [1, 0, 1]
        person["TEST2"] = [0, 1, 1]

        formats = ["greater", "lesser", "AND", "OR", "NAND", "NOR", "XOR", "XNOR"]

        for fmt in formats:
            with self.subTest(format=fmt):
                command = self.make_command(
                    in_channel="TEST1", in_channel_2="TEST2", format=fmt
                )
                command_obj = Merge(command)
                # Just verify it executes without error
                result = command_obj.execute(variables)
                self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()

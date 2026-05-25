import unittest
import numpy as np
from marker import Marker


class MarkerTest(unittest.TestCase):
    def make_variables(self):
        """Create test variables with marker data."""
        variables = {}
        people = []
        person = {
            "FREQUENCY": 10,
            "COLUMNS": ["OTHER", "MARKER_A", "MARKER_B"],
            "FILENAME": "testing",
            "MARKERS": [
                [],  # 0: no markers
                [1],  # 1: marker A at sample 1
                [],  # 2: no markers
                [],  # 3: no markers
                [2],  # 4: marker B at sample 4
                [],  # 5: no markers
                [1],  # 6: marker A at sample 6
                [],  # 7: no markers
                [2, 5],  # 8: markers B and OTHER at sample 8
                [10],  # 9: OTHER marker at sample 9
                [0, 1],  # 10: OTHER and marker A at sample 10
                [3, 2],  # 11: OTHER and marker B at sample 11
                [1],  # 12: marker A at sample 12
                [1],  # 13: marker A at sample 13
                [],  # 14: no markers
                [2],  # 15: marker B at sample 15
            ],
        }
        people.append(person)
        variables["VARNAME"] = people
        return variables

    def make_command(self, **kwargs):
        """Create a command dictionary with overridable defaults."""
        command_data = {
            "class_name": "marker",
            "in": ["VARNAME"],
            "out": ["VARNAME"],
            "in_channel": ["MARKER_A"],
            "in_channel_2": ["MARKER_B"],
            "out_channel": ["OUT"],
            "verbosity": "none",
        }
        command_data.update(kwargs)
        if "name" in command_data.keys():
            command_data["in"] = command_data["name"]
        return command_data

    def test_basic_marker_intervals(self):
        """Test basic marker interval calculation."""
        variables = self.make_variables()
        command_data = self.make_command()

        command = Marker(command_data)
        self.assertTrue(command.good, "Command should be valid")

        result = command.execute(variables)
        person = result["VARNAME"][0]

        # Expected intervals in seconds (samples / frequency):
        # 1. Sample 1 (marker A) → Sample 4 (marker B): 3 samples = 3/10 = 0.3s
        # 2. Sample 6 (marker A) → Sample 8 (marker B): 2 samples = 2/10 = 0.2s
        # 3. Sample 10 (marker A) → Sample 11 (marker B): 1 sample = 1/10 = 0.1s
        # 4. Sample 12 (marker A) → Sample 15 (marker B): 3 samples = 3/10 = 0.3s
        # Note: Sample 13 (marker A) has no following marker B, so not counted

        expected_intervals = [[0.3], [0.2], [0.1], [0.2]]
        self.assertEqual(person["OUT"], expected_intervals)

    def test_reversed_marker_order(self):
        """Test markers in reverse order (A then B, not B then A)."""
        variables = self.make_variables()
        command_data = self.make_command(
            in_channel=["MARKER_B"],  # First look for B
            in_channel_2=["MARKER_A"],  # Then look for A
        )

        command = Marker(command_data)
        result = command.execute(variables)
        person = result["VARNAME"][0]

        # With reversed order: B then A
        # Should find different intervals
        # Sample 4 (B) → Sample 6 (A): 2 samples = 0.2s
        # Sample 8 (B) → Sample 10 (A): 2 samples = 0.2s
        # Sample 11 (B) → Sample 12 (A): 1 sample = 0.1s
        # Sample 15 (B) → no following A, so not counted

        expected_intervals = [[0.2], [0.2], [0.1]]
        self.assertEqual(person["OUT"], expected_intervals)

    def test_no_marker_pairs(self):
        """Test when no marker pairs are found."""
        variables = self.make_variables()

        # Create a person with markers but no pairs
        person = variables["VARNAME"][0].copy()
        person["MARKERS"] = [
            [1],  # Only marker A
            [],
            [3],  # Only marker C
            [1],  # Only marker A
            [],
            [3],  # Only marker C
        ]
        variables["NO_PAIRS"] = [person]

        command_data = self.make_command(
            name=["NO_PAIRS"],
            out=["NO_PAIRS"],
            in_channel=["MARKER_A"],
            in_channel_2=["MARKER_B"],
        )

        command = Marker(command_data)
        result = command.execute(variables)
        person = result["NO_PAIRS"][0]

        # Should return empty list since no A→B pairs
        self.assertEqual(person["OUT"], [])

    def test_consecutive_markers(self):
        """Test with consecutive markers (A immediately followed by B)."""
        variables = self.make_variables()

        # Create a person with consecutive markers
        person = variables["VARNAME"][0].copy()
        person["MARKERS"] = [
            [],  # 0
            [1],  # 1: marker A
            [2],  # 2: marker B (immediately after)
            [],  # 3
            [1],  # 4: marker A
            [2],  # 5: marker B (immediately after)
            [],  # 6
            [1],  # 7: marker A
            [],  # 8
            [2],  # 9: marker B (2 samples after)
        ]
        variables["CONSECUTIVE"] = [person]

        command_data = self.make_command(
            name=["CONSECUTIVE"],
            out=["CONSECUTIVE"],
            in_channel=["MARKER_A"],
            in_channel_2=["MARKER_B"],
        )

        command = Marker(command_data)
        result = command.execute(variables)
        person = result["CONSECUTIVE"][0]

        # Intervals: 1 sample (0.1s), 1 sample (0.1s), 2 samples (0.2s)
        expected_intervals = [[0.1], [0.1], [0.2]]
        self.assertEqual(person["OUT"], expected_intervals)

    def test_marker_with_multiple_columns(self):
        """Test when markers have multiple columns in same sample."""
        variables = self.make_variables()

        # Create markers with multiple columns per sample
        person = variables["VARNAME"][0].copy()
        person["MARKERS"] = [
            [1, 2],  # 0: Both A and B together (time = 0)
            [],  # 1
            [1],  # 2: marker A
            [2],  # 3: marker B (1 sample after)
            [1, 0, 2],  # 4: A, OTHER, and B together (time = 0)
            [1],  # 5: marker A
            [],  # 6
            [2],  # 7: marker B (2 samples after)
        ]
        variables["MULTI_MARKERS"] = [person]

        command_data = self.make_command(
            name=["MULTI_MARKERS"],
            out=["MULTI_MARKERS"],
            in_channel=["MARKER_A"],
            in_channel_2=["MARKER_B"],
        )

        command = Marker(command_data)
        result = command.execute(variables)
        person = result["MULTI_MARKERS"][0]

        # When A and B are in same sample (time=0), that counts as interval of 0
        # Sample 0: A and B together → interval = 0 samples = 0.0s
        # Sample 2: A → Sample 3: B → interval = 1 sample = 0.1s
        # Sample 4: A and B together → interval = 0 samples = 0.0s
        # Sample 5: A → Sample 7: B → interval = 2 samples = 0.2s

        expected_intervals = [[0.0], [0.1], [0.0], [0.2]]
        self.assertEqual(person["OUT"], expected_intervals)

    def test_different_frequency(self):
        """Test with different sampling frequency."""
        variables = self.make_variables()

        # Create person with 100 Hz sampling (10x higher frequency)
        person = variables["VARNAME"][0].copy()
        person["FREQUENCY"] = 100  # 100 Hz
        person["MARKERS"] = [
            [],  # 0
            [1],  # 1: marker A
            [],  # 2
            [],  # 3
            [2],  # 4: marker B (3 samples after)
            [],  # 5
            [1],  # 6: marker A
            [2],  # 7: marker B (1 sample after)
        ]
        variables["HIGH_FREQ"] = [person]

        command_data = self.make_command(
            name=["HIGH_FREQ"],
            out=["HIGH_FREQ"],
            in_channel=["MARKER_A"],
            in_channel_2=["MARKER_B"],
        )

        command = Marker(command_data)
        result = command.execute(variables)
        person = result["HIGH_FREQ"][0]

        # With 100 Hz: 3 samples = 0.03s, 1 sample = 0.01s
        expected_intervals = [[0.03], [0.01]]
        self.assertEqual(person["OUT"], expected_intervals)

    def test_nonexistent_channel(self):
        """Test with non-existent in_channel (should return empty)."""
        variables = self.make_variables()
        command_data = self.make_command(
            in_channel=["NONEXISTENT"], in_channel_2=["MARKER_B"]
        )

        command = Marker(command_data)
        try:
            result = command.execute(variables)
            self.assertIsNone(result)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_both_nonexistent_channels(self):
        """Test with both channels non-existent (should return empty)."""
        variables = self.make_variables()
        command_data = self.make_command(
            in_channel=["NONEXISTENT1"], in_channel_2=["NONEXISTENT2"]
        )

        command = Marker(command_data)
        try:
            result = command.execute(variables)
            self.assertIsNone(result)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_empty_markers_list(self):
        """Test with empty markers list."""
        variables = self.make_variables()

        # Create person with no markers
        person = variables["VARNAME"][0].copy()
        person["MARKERS"] = [[] for _ in range(10)]  # All empty
        variables["NO_MARKERS"] = [person]

        command_data = self.make_command(
            name=["NO_MARKERS"],
            out=["NO_MARKERS"],
            in_channel=["MARKER_A"],
            in_channel_2=["MARKER_B"],
        )

        command = Marker(command_data)
        result = command.execute(variables)
        person = result["NO_MARKERS"][0]

        # Should return empty list
        self.assertEqual(person["OUT"], [])

    def test_multiple_operations(self):
        """Test multiple marker operations in one command."""
        variables = self.make_variables()

        # Create additional test data
        person2 = variables["VARNAME"][0].copy()
        person2["FILENAME"] = "test2"
        person2["MARKERS"] = [
            [1],  # 0: marker A
            [],  # 1
            [2],  # 2: marker B (2 samples after)
        ]
        variables["VARNAME"].append(person2)

        command_data = {
            "class_name": "marker",
            "in": ["VARNAME", "VARNAME"],
            "out": ["RESULT1", "RESULT2"],
            "in_channel": ["MARKER_A", "MARKER_B"],
            "in_channel_2": ["MARKER_B", "MARKER_A"],
            "out_channel": ["A_TO_B", "B_TO_A"],
            "verbosity": "none",
        }

        command = Marker(command_data)
        self.assertTrue(command.good, "Command should be valid")

        result = command.execute(variables)

        # Check first operation: A → B for both people
        person1_result = result["RESULT1"][0]
        person2_result = result["RESULT1"][1]

        # Person 1: [0.3], [0.2], [0.1], [0.3]
        # Person 2: [0.2] (2 samples at 10Hz = 0.2s)

        self.assertEqual(person1_result["A_TO_B"], [[0.3], [0.2], [0.1], [0.2]])
        self.assertEqual(person2_result["A_TO_B"], [[0.2]])

        # Check second operation: B → A for both people
        person1_result = result["RESULT2"][0]
        person2_result = result["RESULT2"][1]

        # Person 1: [0.2], [0.2], [0.1] (from earlier test)
        # Person 2: No B before A, so empty

        self.assertEqual(person1_result["B_TO_A"], [[0.2], [0.2], [0.1]])
        self.assertEqual(person2_result["B_TO_A"], [])

    def test_marker_with_other_columns(self):
        """Test markers with other columns mixed in."""
        variables = self.make_variables()

        # Test with column indices 0 (OTHER) and 5 (non-existent in COLUMNS)
        person = variables["VARNAME"][0].copy()
        person["COLUMNS"] = ["OTHER", "MARKER_A", "MARKER_B", "EXTRA1", "EXTRA2"]
        person["MARKERS"] = [
            [0],  # 0: OTHER only
            [1],  # 1: marker A
            [0, 2],  # 2: OTHER and marker B (1 sample after)
            [4],  # 3: EXTRA2 only
            [1],  # 4: marker A
            [2, 3],  # 5: marker B and EXTRA1 (1 sample after)
            [1, 4],  # 6: marker A and EXTRA2
            [2],  # 7: marker B (1 sample after)
        ]
        variables["MIXED_COLS"] = [person]

        command_data = self.make_command(
            name=["MIXED_COLS"],
            out=["MIXED_COLS"],
            in_channel=["MARKER_A"],
            in_channel_2=["MARKER_B"],
        )

        command = Marker(command_data)
        result = command.execute(variables)
        person = result["MIXED_COLS"][0]

        # Intervals:
        # Sample 1 (A) → Sample 2 (B): 1 sample = 0.1s
        # Sample 4 (A) → Sample 5 (B): 1 sample = 0.1s
        # Sample 6 (A) → Sample 7 (B): 1 sample = 0.1s

        expected_intervals = [[0.1], [0.1], [0.1]]
        self.assertEqual(person["OUT"], expected_intervals)

    def test_marker_reset_logic(self):
        """Test that marker search resets after finding a pair."""
        variables = self.make_variables()

        # Test sequence: A, B, B, A, B
        # Should find: A→B (first pair), then reset and find next A→B
        # Should NOT find: A→B→B or B→A
        person = variables["VARNAME"][0].copy()
        person["MARKERS"] = [
            [],  # 0
            [1],  # 1: marker A
            [],  # 2
            [2],  # 3: marker B (2 samples after)
            [2],  # 4: another marker B (ignored - already found pair)
            [],  # 5
            [1],  # 6: marker A
            [],  # 7
            [2],  # 8: marker B (2 samples after)
        ]
        variables["RESET_TEST"] = [person]

        command_data = self.make_command(
            name=["RESET_TEST"],
            out=["RESET_TEST"],
            in_channel=["MARKER_A"],
            in_channel_2=["MARKER_B"],
        )

        command = Marker(command_data)
        result = command.execute(variables)
        person = result["RESET_TEST"][0]

        # Should find only 2 intervals, not 3
        expected_intervals = [[0.2], [0.2]]
        self.assertEqual(person["OUT"], expected_intervals)


if __name__ == "__main__":
    unittest.main()

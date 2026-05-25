import unittest
import numpy as np

from adjust import Adjust


class AdjustTest(unittest.TestCase):
    def make_variables(self):
        """Create test variables with data, comments, and markers."""
        variables = {}
        people = []

        # Create 10 seconds of data at 100 Hz
        fs = 10
        duration = 10
        n_samples = fs * duration  # 1000 samples
        n_channels = 3

        # Create test data with pattern for verification
        t = np.arange(n_samples) / fs
        data = np.column_stack(
            [
                np.sin(2 * np.pi * 1 * t),  # Channel 1: 1 Hz sine
                np.cos(2 * np.pi * 2 * t),  # Channel 2: 2 Hz cosine
                t,  # Channel 3: Linear ramp
            ]
        )

        # Create comments at specific indices
        comments = [""] * n_samples
        comments[10] = "A"  # 1 second
        comments[50] = "C"  # 5 seconds

        # Initialize with empty lists
        markers = [[] for _ in range(n_samples)]

        # Add frequency markers
        for i in range(n_samples):
            time = i / fs

            # Check 0.5 Hz (every 2 seconds)
            if time > 0 and time % 2 == 0:
                markers[i].append(2)

            # Check 1 Hz (every 1 second)
            if time > 0 and time % 1 == 0:
                markers[i].append(0)

            # Check 2 Hz (every 0.5 seconds)
            if time > 0 and time % 0.5 == 0:
                markers[i].append(1)

        person = {}
        person["FREQUENCY"] = fs
        person["FILENAME"] = "test_recording"
        person["DATA"] = data
        person["COMMENTS"] = comments
        person["MARKERS"] = markers
        person["COLUMNS"] = ["1HZ", "2HZ", "RAMP"]

        people.append(person)
        variables["TEST_DATA"] = people
        variables["TEST_DATA2"] = people

        return variables

    def make_command(self, **kwargs):
        """Create a command dictionary with overridable defaults."""
        command_data = {}
        command_data["class_name"] = "cut"
        command_data["in"] = "TEST_DATA"
        command_data["in_2"] = "TEST_DATA2"
        command_data["out"] = "TEST_DATA"
        command_data["comments"] = "A"
        command_data["in_channel"] = "1hz"
        command_data["in_channel_2"] = "1hz"
        command_data["out_channel"] = "new"
        command_data["verbosity"] = "none"
        command_data.update(kwargs)
        if "name" in command_data:
            command_data["in"] = command_data["name"]
        return command_data

    def test_basic_adjustment(self):
        """Test basic adjustment functionality."""
        variables = self.make_variables()
        command_data = self.make_command()

        command = Adjust(command_data)
        self.assertTrue(command.good, "Command should be valid")

        result = command.execute(variables)
        person = result["TEST_DATA"][0]
        self.assertEqual(len(person["COLUMNS"]), 4)

        column = person["DATA"][0:10, 3]
        data = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        np.testing.assert_array_almost_equal(column, data, decimal=10)

        column = person["DATA"][10:100, 3]
        data = person["DATA"][0:90, 0]
        np.testing.assert_array_almost_equal(column, data, decimal=10)

    def test_adjustment_with_different_comment(self):
        """Test adjustment using comment C at index 50."""
        variables = self.make_variables()
        command_data = self.make_command(comments=["C"])

        command = Adjust(command_data)
        self.assertTrue(command.good, "Command should be valid")

        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        # New column should exist
        self.assertEqual(len(person["COLUMNS"]), 4)

        # Check values before comment C (index 50) are zeros
        column_before = person["DATA"][0:50, 3]
        expected_before = np.zeros(50)
        np.testing.assert_array_almost_equal(column_before, expected_before, decimal=10)

        # Check values after comment C
        # We copy from reference starting at index 0 into target starting at index 50
        # Only 50 samples left (100 total - 50 start)
        column_after = person["DATA"][50:100, 3]  # Indices 50-99
        source_data = person["DATA"][0:50, 0]  # First 50 values from 1HZ channel
        np.testing.assert_array_almost_equal(column_after, source_data, decimal=10)

    def test_adjustment_with_missing_comment(self):
        """No comment for D, it should default to going back to origin"""
        variables = self.make_variables()
        command_data = self.make_command(comments=["D"], in_channel_2="")

        command = Adjust(command_data)
        self.assertTrue(command.good, "Command should be valid")

        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        # New column should exist
        self.assertEqual(len(person["COLUMNS"]), 4)

        column_after = person["DATA"][0:100, 3]  # Indices 50-99
        source_data = person["DATA"][0:100, 0]  # First 50 values from 1HZ channel
        np.testing.assert_array_almost_equal(column_after, source_data, decimal=10)

    def test_adjustment_overwriting(self):
        """Test adjustment using comment C at index 50."""
        variables = self.make_variables()
        command_data = self.make_command(out_channel=["1HZ"])

        command = Adjust(command_data)
        self.assertTrue(command.good, "Command should be valid")

        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        # New column should exist
        self.assertEqual(len(person["COLUMNS"]), 3)

        column_after = person["DATA"][10:20, 0]
        source_data = person["DATA"][0:10, 0]
        np.testing.assert_array_almost_equal(column_after, source_data, decimal=10)


if __name__ == "__main__":
    unittest.main()

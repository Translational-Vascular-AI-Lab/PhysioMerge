import unittest
import numpy as np
from statistics import mode, median, mean

# Adjust import path as needed
from measurement import Measurement


class MeasurementTest(unittest.TestCase):
    def make_variables(self):
        """Create test variables with three different channels."""
        variables = {}
        people = []

        # Test data as specified
        channel1 = [10, 5, -10, 10, 15, 20, 25, 10, -10]
        channel2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        channel3 = [1, 1, 1, 2, 2, 1, 1, 1, 2, 2, 5]

        person = {
            "FREQUENCY": 100,  # 100 Hz sampling frequency
            "FILENAME": "test_person",
            "CHANNEL1": [channel1],
            "CHANNEL2": [channel2],
            "CHANNEL3": [channel3],
        }

        people.append(person)
        variables["TEST_DATA"] = people
        return variables

    def make_command(self, **kwargs):
        """Create a command dictionary with overridable defaults."""
        command_data = {
            "class_name": "measurement",
            "in": ["TEST_DATA"],
            "out": ["MEASURED_DATA"],
            "in_channel": ["CHANNEL1"],
            "out_channel": ["RESULT"],
            "format": "mean",
            "verbosity": "none",
        }
        command_data.update(kwargs)
        return command_data

    def calculate_expected(self, data, format_str, frequency=100):
        """Calculate expected result for a given format."""
        if not data:
            return [0]

        if format_str == "mean":
            return [mean(data)]
        elif format_str == "mode":
            return [mode(data)]
        elif format_str == "median":
            return [median(data)]
        elif format_str == "min":
            return [min(data)]
        elif format_str == "max":
            return [max(data)]
        elif format_str == "period":
            return [len(data) / frequency]
        elif format_str == "amplitude":
            return [max(data) - min(data)]
        elif format_str == "frequency":
            return [frequency / len(data)]
        else:
            raise ValueError(f"Unknown format: {format_str}")

    def test_all_formats_for_channel1(self):
        """Test all formats for Channel 1."""
        variables = self.make_variables()
        channel_data = variables["TEST_DATA"][0]["CHANNEL1"][0]
        frequency = variables["TEST_DATA"][0]["FREQUENCY"]

        formats_to_test = [
            "mean",
            "median",
            "min",
            "max",
            "period",
            "amplitude",
            "frequency",
        ]

        for fmt in formats_to_test:
            expected = self.calculate_expected(channel_data, fmt, frequency)

            command_data = self.make_command(
                in_channel=["CHANNEL1"],
                out_channel=[f"{fmt.upper()}_RESULT"],
                format=fmt,
            )

            command = Measurement(command_data)
            result = command.execute(
                variables.copy()
            )  # Use copy to avoid contamination
            person = result["MEASURED_DATA"][0]

            self.assertIn(f"{fmt.upper()}_RESULT", person)

            # For mode, we might get an exception - handle separately
            if fmt == "mode":
                print(f"Mode result: {person[f'{fmt.upper()}_RESULT']}")
            else:
                self.assertAlmostEqual(
                    person[f"{fmt.upper()}_RESULT"][0][0],
                    expected[0],
                    places=10,
                    msg=f"Failed for format '{fmt}'",
                )

    def test_all_formats_for_channel2(self):
        """Test all formats for Channel 2."""
        variables = self.make_variables()
        channel2_data = variables["TEST_DATA"][0]["CHANNEL2"][0]
        frequency = variables["TEST_DATA"][0]["FREQUENCY"]

        formats_to_test = [
            "mean",
            "median",
            "min",
            "max",
            "period",
            "amplitude",
            "frequency",
        ]

        for fmt in formats_to_test:
            expected = self.calculate_expected(channel2_data, fmt, frequency)

            command_data = self.make_command(
                in_channel=["CHANNEL2"],
                out_channel=[f"{fmt.upper()}_RESULT"],
                format=fmt,
            )

            command = Measurement(command_data)
            result = command.execute(
                variables.copy()
            )  # Use copy to avoid contamination
            person = result["MEASURED_DATA"][0]

            self.assertIn(f"{fmt.upper()}_RESULT", person)

            # For mode, we might get an exception - handle separately
            if fmt == "mode":
                print(f"Mode result: {person[f'{fmt.upper()}_RESULT']}")
            else:
                self.assertAlmostEqual(
                    person[f"{fmt.upper()}_RESULT"][0][0],
                    expected[0],
                    places=10,
                    msg=f"Failed for format '{fmt}'",
                )

    def test_all_formats_for_channel3(self):
        """Test all formats for Channel 3."""
        variables = self.make_variables()
        channel_data = variables["TEST_DATA"][0]["CHANNEL3"][0]
        frequency = variables["TEST_DATA"][0]["FREQUENCY"]

        formats_to_test = [
            "mean",
            "median",
            "min",
            "max",
            "period",
            "amplitude",
            "frequency",
        ]

        for fmt in formats_to_test:
            expected = self.calculate_expected(channel_data, fmt, frequency)

            command_data = self.make_command(
                in_channel=["CHANNEL3"],
                out_channel=[f"{fmt.upper()}_RESULT"],
                format=fmt,
            )

            command = Measurement(command_data)
            result = command.execute(
                variables.copy()
            )  # Use copy to avoid contamination
            person = result["MEASURED_DATA"][0]

            self.assertIn(f"{fmt.upper()}_RESULT", person)

            # For mode, we might get an exception - handle separately
            if fmt == "mode":
                print(f"Mode result: {person[f'{fmt.upper()}_RESULT']}")
            else:
                self.assertAlmostEqual(
                    person[f"{fmt.upper()}_RESULT"][0][0],
                    expected[0],
                    places=10,
                    msg=f"Failed for format '{fmt}'",
                )

    def test_multiple_operations(self):
        """Test multiple measurement operations in one command."""
        variables = self.make_variables()

        command_data = {
            "class_name": "measurement",
            "in": ["TEST_DATA", "TEST_DATA", "TEST_DATA"],
            "out": ["RESULT1", "RESULT2", "RESULT3"],
            "in_channel": ["CHANNEL1", "CHANNEL2", "CHANNEL3"],
            "out_channel": ["CH1_MEAN", "CH2_MEDIAN", "CH3_MAX"],
            "format": ["mean", "median", "max"],
            "verbosity": "none",
        }

        command = Measurement(command_data)
        self.assertTrue(command.good, "Command should be valid")

        result = command.execute(variables)

        # Check all three results
        person1 = result["RESULT1"][0]
        person2 = result["RESULT2"][0]
        person3 = result["RESULT3"][0]

        # Calculate expected values
        ch1_data = variables["TEST_DATA"][0]["CHANNEL1"][0]
        ch2_data = variables["TEST_DATA"][0]["CHANNEL2"][0]
        ch3_data = variables["TEST_DATA"][0]["CHANNEL3"][0]

        expected_ch1_mean = mean(ch1_data)
        expected_ch2_median = median(ch2_data)
        expected_ch3_max = max(ch3_data)

        self.assertAlmostEqual(person1["CH1_MEAN"][0][0], expected_ch1_mean, places=10)
        self.assertAlmostEqual(
            person2["CH2_MEDIAN"][0][0], expected_ch2_median, places=10
        )
        self.assertAlmostEqual(person3["CH3_MAX"][0][0], expected_ch3_max, places=10)

    def test_invalid_format_string(self):
        """Test with invalid format string (should fail validation)."""
        command_data = self.make_command(format="invalid_format")

        # Execute should return variables unchanged
        variables = self.make_variables()
        try:
            command = Measurement(command_data)
            result = command.execute(variables)
            self.assertIsNone(result)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_invalid_format_type(self):
        """Test with invalid format type (e.g., integer)."""
        command_data = self.make_command()
        command_data["format"] = 123

        try:
            command = Measurement(command_data)
            self.assertIsNone(command)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_empty_channel(self):
        """Test measurement on empty channel (should return [0])."""
        variables = self.make_variables()

        # Add an empty channel
        person = variables["TEST_DATA"][0]
        person["EMPTY_CHANNEL"] = []

        command_data = self.make_command(
            in_channel=["EMPTY_CHANNEL"], out_channel=["EMPTY_RESULT"], format="mean"
        )

        command = Measurement(command_data)
        result = command.execute(variables)
        person = result["MEASURED_DATA"][0]

        # Empty channel should return [0]
        self.assertEqual(person["EMPTY_RESULT"], [])

    def test_nonexistent_channel(self):
        """Test measurement on non-existent channel (should print error)."""
        variables = self.make_variables()

        command_data = self.make_command(
            in_channel=["NONEXISTENT"], out_channel=["NO_RESULT"], format="mean"
        )

        command = Measurement(command_data)
        # Command should still be valid
        self.assertTrue(command.good)

        try:
            result = command.execute(variables)
            self.assertisnone(result)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_format_as_list(self):
        """Test format specified as a list."""
        variables = self.make_variables()

        command_data = {
            "class_name": "measurement",
            "in": ["TEST_DATA", "TEST_DATA"],
            "out": ["OUT1", "OUT2"],
            "in_channel": ["CHANNEL1", "CHANNEL2"],
            "out_channel": ["CH1_MIN", "CH2_MAX"],
            "format": ["min", "max"],
            "verbosity": "none",
        }

        command = Measurement(command_data)
        self.assertTrue(command.good, "Command should be valid")

        result = command.execute(variables)

        person1 = result["OUT1"][0]
        person2 = result["OUT2"][0]

        ch1_min = min(variables["TEST_DATA"][0]["CHANNEL1"][0])
        ch2_max = max(variables["TEST_DATA"][0]["CHANNEL2"][0])

        self.assertEqual(person1["CH1_MIN"][0][0], ch1_min)
        self.assertEqual(person2["CH2_MAX"][0][0], ch2_max)


if __name__ == "__main__":
    unittest.main()

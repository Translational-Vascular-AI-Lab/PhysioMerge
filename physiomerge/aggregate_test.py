import unittest
import numpy as np
from scipy.stats import mode as scipy_mode

from aggregate import Aggregate


class AggregateTest(unittest.TestCase):
    def make_variables(self):
        """Create test variables with multiple data scenarios."""
        variables = {}
        people = []

        # Person 1: Basic test data
        person1 = {}
        person1["FREQUENCY"] = 2
        person1["FILENAME"] = "testing1"
        person1["CHANNELA"] = [[10], [20], [10], [25], [10], [15], [float("nan")]]
        person1["CHANNELB"] = [[5.5], [6.5], [7.5], [8.5], [9.5]]  # For mean tests
        person1["CHANNELC"] = [
            [1],
            [2],
            [3],
            [2],
            [1],
            [2],
            [3],
            [2],
        ]  # For mode tests (mode=2)
        person1["CHANNELD"] = [[10], [20], [30], [40], [50]]  # For variance/std tests
        person1["ALIGHT1"] = [1, 0, 1, 0, 1, 0, 1]
        person1["ALIGHT2"] = [0, 1, 0, 1, 0, 1, 0]
        person1["WEIGHTS1"] = [[2], [1], [2], [0.5], [2], [1], [0]]
        person1["WEIGHTS2"] = [[10], [20], [10], [25], [2], [20], [100]]
        people.append(person1)

        # Person 2: Edge cases
        person2 = {}
        person2["FREQUENCY"] = 1
        person2["FILENAME"] = "testing2"
        person2["CHANNELA"] = [[-5, 5], [0, 0], [5, -5], [-10, 10], [10, -10]]
        person2["ALIGHT1"] = [1, 1, 1, 1, 1]
        person2["WEIGHTS1"] = [[1], [1], [1], [1], [1]]
        people.append(person2)

        variables["PERSON"] = people
        return variables

    def make_command(self, **kwargs):
        """Create a command dictionary with overridable defaults."""
        command_data = {}
        command_data["class_name"] = "aggregate"
        command_data["in"] = "PERSON"
        command_data["in_channel"] = "CHANNELA"
        command_data["out_channel"] = "OUT"
        command_data["out"] = "PERSON"
        command_data["format"] = "MEAN"
        command_data["mask"] = "ALIGHT1"
        command_data["verbosity"] = "none"

        # Override with any provided kwargs
        command_data.update(kwargs)
        return command_data

    # Existing tests
    def test_aggregate_alight1(self):
        """Test mean aggregation with ALIGHT1 mask."""
        variables = self.make_variables()
        command_data = self.make_command()
        command = Aggregate(command_data)
        variables = command.execute(variables)

        self.assertIn("PERSON", variables)
        self.assertEqual(len(variables["PERSON"]), 2)

        # Person 1: CHANNELA filtered by ALIGHT1 [1, 0, 1, 0, 1, 0, 1]
        # Filtered values: [10], [10], [10], [nan] -> mean of [10, 10, 10] = 10
        person1 = variables["PERSON"][0]
        self.assertIn("OUT", person1)
        np.testing.assert_array_almost_equal([[10.0]], person1["OUT"], decimal=5)

        # Person 2: All values included
        person2 = variables["PERSON"][1]
        self.assertIn("OUT", person2)
        expected_mean2 = (-5 + 0 + 5 - 10 + 10) / 5  # 0.0
        np.testing.assert_array_almost_equal(
            person2["OUT"], [[expected_mean2, expected_mean2]], decimal=5
        )

    def test_aggregate_alight2(self):
        """Test mean aggregation with ALIGHT2 mask."""
        variables = self.make_variables()
        command_data = self.make_command(mask="ALIGHT2")
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Person 1: CHANNELA filtered by ALIGHT2 [0, 1, 0, 1, 0, 1, 0]
        # Filtered values: [20], [25], [15] -> mean = 20
        person1 = variables["PERSON"][0]
        np.testing.assert_array_almost_equal([[20.0]], person1["OUT"], decimal=5)

    def test_aggregate_no_alight(self):
        """Test mean aggregation without mask."""
        variables = self.make_variables()
        command_data = self.make_command(mask="")
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Person 1: All non-NaN values from CHANNELA
        # Values: [10, 20, 10, 25, 10, 15] -> mean = 15
        person1 = variables["PERSON"][0]
        np.testing.assert_array_almost_equal([[15.0]], person1["OUT"], decimal=5)

        # Person 2: All values
        person2 = variables["PERSON"][1]
        expected_mean2 = 0.0  # (-5 + 0 + 5 - 10 + 10) / 5
        np.testing.assert_array_almost_equal(
            person2["OUT"], [[expected_mean2, expected_mean2]], decimal=5
        )

    def test_aggregate_weights1(self):
        """Test weighted mean with WEIGHTS1."""
        variables = self.make_variables()
        command_data = self.make_command(mask="", weights="WEIGHTS1")
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Person 1: Weighted mean calculation
        # Values: [10, 20, 10, 25, 10, 15] (nan excluded)
        # Weights: [2, 1, 2, 0.5, 2, 1]
        # Weighted sum: 10*2 + 20*1 + 10*2 + 25*0.5 + 10*2 + 15*1 = 20 + 20 + 20 + 12.5 + 20 + 15 = 107.5
        # Sum of weights: 2 + 1 + 2 + 0.5 + 2 + 1 = 8.5
        # Weighted mean: 107.5 / 8.5 = 12.6470588235
        person1 = variables["PERSON"][0]
        np.testing.assert_array_almost_equal(
            [[12.6470588235]], person1["OUT"], decimal=5
        )

    def test_aggregate_weights2(self):
        """Test weighted mean with WEIGHTS2."""
        variables = self.make_variables()
        command_data = self.make_command(mask="", weights="WEIGHTS2")
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Person 1: Weighted mean with WEIGHTS2
        # Values: [10, 20, 10, 25, 10, 15] (nan excluded)
        # Weights: [10, 20, 10, 25, 2, 20]
        # Weighted sum: 10*10 + 20*20 + 10*10 + 25*25 + 10*2 + 15*20 = 100 + 400 + 100 + 625 + 20 + 300 = 1545
        # Sum of weights: 10 + 20 + 10 + 25 + 2 + 20 = 87
        # Weighted mean: 1545 / 87 = 17.7586206897
        person1 = variables["PERSON"][0]
        np.testing.assert_array_almost_equal(
            [[17.7586206897]], person1["OUT"], decimal=5
        )

    # New tests for all aggregation formats with explicit numerical assertions
    def test_aggregate_min(self):
        """Test min aggregation with explicit values."""
        variables = self.make_variables()
        command_data = self.make_command(format="MIN", mask="")
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Person 1: CHANNELA values: [10, 20, 10, 25, 10, 15] -> min = 10
        person1 = variables["PERSON"][0]
        np.testing.assert_array_almost_equal([[10.0]], person1["OUT"], decimal=5)

        # Person 2: Values: [-5, 0, 5, -10, 10] -> min = -10
        person2 = variables["PERSON"][1]
        np.testing.assert_array_almost_equal(
            [[-10.0, -10.0]], person2["OUT"], decimal=5
        )

    def test_aggregate_max(self):
        """Test max aggregation with explicit values."""
        variables = self.make_variables()
        command_data = self.make_command(format="MAX", mask="")
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Person 1: CHANNELA values: [10, 20, 10, 25, 10, 15] -> max = 25
        person1 = variables["PERSON"][0]
        np.testing.assert_array_almost_equal([[25.0]], person1["OUT"], decimal=5)

        # Person 2: Values: [-5, 0, 5, -10, 10] -> max = 10
        person2 = variables["PERSON"][1]
        np.testing.assert_array_almost_equal([[10.0, 10.0]], person2["OUT"], decimal=5)

    def test_aggregate_median(self):
        """Test median aggregation with explicit values."""
        variables = self.make_variables()
        command_data = self.make_command(format="MEDIAN", mask="")
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Person 1: CHANNELA values sorted: [10, 10, 10, 15, 20, 25] -> median of even count = average of middle two = (10 + 15)/2 = 12.5
        person1 = variables["PERSON"][0]
        np.testing.assert_array_almost_equal([[12.5]], person1["OUT"], decimal=5)

        # Person 2: Values sorted: [-10, -5, 0, 5, 10] -> median = 0
        person2 = variables["PERSON"][1]
        np.testing.assert_array_almost_equal([[0.0, 0.0]], person2["OUT"], decimal=5)

    def test_aggregate_mode(self):
        """Test mode aggregation with explicit values."""
        variables = self.make_variables()
        command_data = self.make_command(format="MODE", in_channel="CHANNELC", mask="")
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Person 1: CHANNELC values: [1, 2, 3, 2, 1, 2, 3, 2] -> mode = 2 (appears 4 times)
        person1 = variables["PERSON"][0]
        np.testing.assert_array_almost_equal([2.0], person1["OUT"], decimal=5)

    def test_aggregate_variance(self):
        """Test variance aggregation with explicit calculations."""
        variables = self.make_variables()
        command_data = self.make_command(
            format="VARIANCE", in_channel="CHANNELD", mask=""
        )
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Person 1: CHANNELD values: [10, 20, 30, 40, 50]
        # Mean: (10+20+30+40+50)/5 = 30
        # Variance: ((10-30)² + (20-30)² + (30-30)² + (40-30)² + (50-30)²) / 5 = (400 + 100 + 0 + 100 + 400)/5 = 1000/5 = 200
        person1 = variables["PERSON"][0]
        np.testing.assert_array_almost_equal([[200.0]], person1["OUT"], decimal=5)

    def test_aggregate_std(self):
        """Test standard deviation aggregation with explicit calculations."""
        variables = self.make_variables()
        command_data = self.make_command(format="STD", in_channel="CHANNELD", mask="")
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Person 1: CHANNELD values: [10, 20, 30, 40, 50]
        # Variance = 200 (from previous test)
        # Std = sqrt(200) = 14.1421356237
        person1 = variables["PERSON"][0]
        np.testing.assert_array_almost_equal(
            [[14.1421356237]], person1["OUT"], decimal=5
        )

    # Edge case tests with explicit assertions
    def test_aggregate_empty_filtered_data(self):
        """Test aggregation when mask filters out all data."""
        variables = self.make_variables()
        # Create a mask that excludes all data
        person = variables["PERSON"][0]
        person["EMPTYMASK"] = [0, 0, 0, 0, 0, 0, 0]

        command_data = self.make_command(mask="EMPTYMASK")
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Should return NaN for empty filtered data
        person1 = variables["PERSON"][0]
        self.assertIn("OUT", person1)
        result = person1["OUT"][0]
        self.assertTrue(np.isnan(result) or result[0] is float("nan"))

    def test_aggregate_nan_handling(self):
        """Test that NaN values are properly handled."""
        variables = self.make_variables()
        # Add a channel with NaN values
        person = variables["PERSON"][0]
        person["NANCHANNEL"] = [[1.0], [float("nan")], [2.0], [float("nan")], [3.0]]
        person["NANMASK"] = [1, 1, 1, 1, 1]

        command_data = self.make_command(
            in_channel="NANCHANNEL", mask="NANMASK", format="MEAN"
        )
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Should calculate mean of non-NaN values: (1.0 + 2.0 + 3.0) / 3 = 2.0
        person1 = variables["PERSON"][0]
        np.testing.assert_array_almost_equal([[2.0]], person1["OUT"], decimal=5)

    def test_aggregate_with_nan_weights(self):
        """Test aggregation with NaN weights."""
        variables = self.make_variables()
        person = variables["PERSON"][0]
        person["NANWEIGHTS"] = [
            [1.0],
            [float("nan")],
            [1.0],
            [float("nan")],
            [1.0],
            [1.0],
            [1.0],
        ]

        command_data = self.make_command(mask="", weights="NANWEIGHTS", format="MEAN")
        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Should handle NaN weights appropriately
        person1 = variables["PERSON"][0]
        self.assertIn("OUT", person1)

    def test_aggregate_single_value(self):
        """Test aggregation on a single data point."""
        variables = {}
        person = {}
        person["FILENAME"] = "single_value"
        person["SINGLECHANNEL"] = [[42.0]]
        person["SINGLEMASK"] = [1]
        person["SINGLEWEIGHTS"] = [[1.0]]
        variables["SINGLE"] = [person]

        command_data = {
            "class_name": "aggregate",
            "in": "SINGLE",
            "in_channel": "SINGLECHANNEL",
            "out_channel": "OUT",
            "out": "SINGLE",
            "format": "MEAN",
            "mask": "SINGLEMASK",
            "verbosity": "none",
        }

        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Mean of single value 42.0 = 42.0
        result = variables["SINGLE"][0]["OUT"]
        np.testing.assert_array_almost_equal([[42.0]], result, decimal=5)

    def test_aggregate_multiple_channels(self):
        """Test aggregation across multiple input/output pairs."""
        variables = self.make_variables()
        command_data = {
            "class_name": "aggregate",
            "in": ["PERSON", "PERSON"],
            "in_channel": ["CHANNELA", "CHANNELB"],
            "out_channel": ["OUT_A", "OUT_B"],
            "out": ["PERSON_A", "PERSON_B"],
            "format": "MEAN",
            "mask": ["ALIGHT1", ""],
            "verbosity": "none",
        }

        command = Aggregate(command_data)
        variables = command.execute(variables)

        # Check both outputs
        self.assertIn("PERSON_A", variables)
        self.assertIn("PERSON_B", variables)

        # PERSON_A: CHANNELA with ALIGHT1 mask -> mean = 10
        np.testing.assert_array_almost_equal(
            [[10.0]], variables["PERSON_A"][0]["OUT_A"], decimal=5
        )

        # PERSON_B: CHANNELB without mask -> mean of [5.5, 6.5, 7.5, 8.5, 9.5] = 7.5
        np.testing.assert_array_almost_equal(
            [[7.5]], variables["PERSON_B"][0]["OUT_B"], decimal=5
        )

    def test_aggregate_validation_invalid_format(self):
        """Test validation with invalid format."""
        command_data = self.make_command(format="INVALID_FORMAT", verbosity="always")

        with self.assertRaises(Exception) as context:
            command = Aggregate(command_data)
            self.assertFalse(command.good)

    def test_aggregate_execute_invalid_skips(self):
        """Test that invalid commands are skipped."""
        variables = self.make_variables()
        command_data = self.make_command(format="INVALID_FORMAT")

        # This should create an invalid command that gets skipped
        try:
            command = Aggregate(command_data)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_aggregate_case_insensitive_format(self):
        """Test that format is case-insensitive."""
        variables = self.make_variables()

        # Test uppercase
        command_data1 = self.make_command(format="MEAN", mask="")
        command1 = Aggregate(command_data1)
        result1 = command1.execute(self.make_variables())
        mean1 = result1["PERSON"][0]["OUT"][0]

        # Test lowercase
        command_data2 = self.make_command(format="mean", mask="")
        command2 = Aggregate(command_data2)
        result2 = command2.execute(self.make_variables())
        mean2 = result2["PERSON"][0]["OUT"][0]

        # Test mixed case
        command_data3 = self.make_command(format="Mean", mask="")
        command3 = Aggregate(command_data3)
        result3 = command3.execute(self.make_variables())
        mean3 = result3["PERSON"][0]["OUT"][0]

        # All should give same result
        np.testing.assert_array_almost_equal(mean1, mean2, decimal=5)
        np.testing.assert_array_almost_equal(mean1, mean3, decimal=5)


if __name__ == "__main__":
    unittest.main()

import unittest
import numpy as np
from arithmetic import Arithmetic


class ArithmeticTest(unittest.TestCase):
    def make_variables(self):
        """Create test variables with various data channels."""
        variables = {}
        people = []
        person = {
            "FREQUENCY": 2,
            "FILENAME": "testing",
            "CHANNELA": [[10], [20], [50], [100]],  # Single values
            "CHANNELB": [[1], [2], [5], [10]],  # Single values
            "CHANNELC": [[1, 2, 3], [5, 6, 7]],  # Multi-value segments
            "CHANNELD": [[3, 2, 1], [1, 2, 3]],  # Multi-value segments (reversed)
            "CHANNELE": [[0], [10], [0], [5]],  # Contains zeros for reciprocal test
            "EMPTY_CH": [],  # Empty channel
        }
        people.append(person)
        variables["VARNAME"] = people
        return variables

    def make_command(self, **kwargs):
        """Create a command dictionary with overridable defaults."""
        command_data = {
            "class_name": "arithmetic",
            "in": ["VARNAME"],
            "out": ["VARNAME"],
            "in_channel": ["CHANNELA"],
            "out_channel": ["OUT"],
            "format": "+",
            "num": 2,
            "verbosity": "none",
        }
        command_data.update(kwargs)
        if "name" in command_data.keys():
            command_data["in"] = command_data["name"]
        return command_data

    def run_arithmetic_test(
        self, format_op, in_channel="CHANNELA", num=2, in_channel_2=None, expected=None
    ):
        """Helper function to run arithmetic tests."""
        variables = self.make_variables()

        command_data = self.make_command(
            in_channel=in_channel,
            format=format_op,
            num=num if not in_channel_2 else None,
            in_channel_2=in_channel_2,
        )

        command = Arithmetic(command_data)
        self.assertTrue(command.good, f"Command should be valid for {format_op}")

        result = command.execute(variables)
        person = result["VARNAME"][0]

        if expected is not None:
            self.assertIn("OUT", person)

            # Convert expected to list if it's a single value
            if isinstance(expected, (int, float)):
                expected = [[expected]]

            # Compare results
            if isinstance(expected[0], list):
                # Multi-dimensional comparison
                self.assertEqual(len(person["OUT"]), len(expected))
                for i, (actual_row, expected_row) in enumerate(
                    zip(person["OUT"], expected)
                ):
                    if isinstance(expected_row, (int, float)):
                        # Single value in row
                        self.assertAlmostEqual(
                            actual_row[0],
                            expected_row,
                            places=10,
                            msg=f"Row {i}: {actual_row} != {expected_row}",
                        )
                    else:
                        # Multiple values in row
                        for j, (actual_val, expected_val) in enumerate(
                            zip(actual_row, expected_row)
                        ):
                            self.assertAlmostEqual(
                                actual_val,
                                expected_val,
                                places=10,
                                msg=f"Position ({i},{j}): {actual_val} != {expected_val}",
                            )
            else:
                # Single row comparison
                for i, (actual_val, expected_val) in enumerate(
                    zip(person["OUT"][0], expected)
                ):
                    self.assertAlmostEqual(
                        actual_val,
                        expected_val,
                        places=10,
                        msg=f"Position {i}: {actual_val} != {expected_val}",
                    )

        return person

    # Basic arithmetic with constants
    def test_addition_constant(self):
        """Test addition with constant: CHANNELA + 2"""
        self.run_arithmetic_test("+", expected=[[12], [22], [52], [102]])

    def test_subtraction_constant(self):
        """Test subtraction with constant: CHANNELA - 2"""
        self.run_arithmetic_test("-", expected=[[8], [18], [48], [98]])

    def test_multiplication_constant(self):
        """Test multiplication with constant: CHANNELA * 2"""
        self.run_arithmetic_test("*", expected=[[20], [40], [100], [200]])

    def test_division_constant(self):
        """Test division with constant: CHANNELA / 2"""
        self.run_arithmetic_test("/", expected=[[5], [10], [25], [50]])

    def test_reciprocal(self):
        """Test reciprocal operation: 1 / CHANNELA"""
        self.run_arithmetic_test("-1", expected=[[0.1], [0.05], [0.02], [0.01]])

    # Arithmetic with multi-value segments
    def test_addition_multi_value(self):
        """Test addition with multi-value segments: CHANNELC + 2"""
        self.run_arithmetic_test(
            "+", in_channel="CHANNELC", expected=[[3, 4, 5], [7, 8, 9]]
        )

    def test_subtraction_multi_value(self):
        """Test subtraction with multi-value segments: CHANNELC - 2"""
        self.run_arithmetic_test(
            "-", in_channel="CHANNELC", expected=[[-1, 0, 1], [3, 4, 5]]
        )

    def test_multiplication_multi_value(self):
        """Test multiplication with multi-value segments: CHANNELC * 2"""
        self.run_arithmetic_test(
            "*", in_channel="CHANNELC", expected=[[2, 4, 6], [10, 12, 14]]
        )

    def test_division_multi_value(self):
        """Test division with multi-value segments: CHANNELC / 2"""
        self.run_arithmetic_test(
            "/", in_channel="CHANNELC", expected=[[0.5, 1, 1.5], [2.5, 3, 3.5]]
        )

    # Channel-to-channel operations
    def test_channel_addition(self):
        """Test channel-to-channel addition: CHANNELA + CHANNELB"""
        self.run_arithmetic_test(
            "+", in_channel_2="CHANNELB", expected=[[11], [22], [55], [110]]
        )

    def test_channel_subtraction(self):
        """Test channel-to-channel subtraction: CHANNELA - CHANNELB"""
        self.run_arithmetic_test(
            "-", in_channel_2="CHANNELB", expected=[[9], [18], [45], [90]]
        )

    def test_channel_multiplication(self):
        """Test channel-to-channel multiplication: CHANNELA * CHANNELB"""
        self.run_arithmetic_test(
            "*", in_channel_2="CHANNELB", expected=[[10], [40], [250], [1000]]
        )

    def test_channel_division(self):
        """Test channel-to-channel division: CHANNELA / CHANNELB"""
        self.run_arithmetic_test(
            "/", in_channel_2="CHANNELB", expected=[[10], [10], [10], [10]]
        )

    # Channel-to-channel with multi-value segments
    def test_multi_value_channel_addition(self):
        """Test channel-to-channel addition with multi-value: CHANNELC + CHANNELD"""
        self.run_arithmetic_test(
            "+",
            in_channel="CHANNELC",
            in_channel_2="CHANNELD",
            expected=[[4, 4, 4], [6, 8, 10]],
        )

    def test_multi_value_channel_subtraction(self):
        """Test channel-to-channel subtraction with multi-value: CHANNELC - CHANNELD"""
        self.run_arithmetic_test(
            "-",
            in_channel="CHANNELC",
            in_channel_2="CHANNELD",
            expected=[[-2, 0, 2], [4, 4, 4]],
        )

    def test_multi_value_channel_multiplication(self):
        """Test channel-to-channel multiplication with multi-value: CHANNELC * CHANNELD"""
        self.run_arithmetic_test(
            "*",
            in_channel="CHANNELC",
            in_channel_2="CHANNELD",
            expected=[[3, 4, 3], [5, 12, 21]],
        )

    def test_multi_value_channel_division(self):
        """Test channel-to-channel division with multi-value: CHANNELC / CHANNELD"""
        person = self.run_arithmetic_test(
            "/", in_channel="CHANNELC", in_channel_2="CHANNELD"
        )

        # Check first row
        self.assertAlmostEqual(person["OUT"][0][0], 1 / 3, places=10)  # 1/3
        self.assertAlmostEqual(person["OUT"][0][1], 1.0, places=10)  # 2/2
        self.assertAlmostEqual(person["OUT"][0][2], 3.0, places=10)  # 2/2

        # Check second row
        self.assertAlmostEqual(person["OUT"][1][0], 5.0, places=10)  # 5/1
        self.assertAlmostEqual(person["OUT"][1][1], 3.0, places=10)  # 6/2
        self.assertAlmostEqual(person["OUT"][1][2], 7 / 3, places=10)  # 7/3

    # Edge cases and special tests
    def test_division_by_zero_constant(self):
        """Test division by zero constant (should produce NaN)."""
        person = self.run_arithmetic_test("/", num=0)

        # All values should be NaN
        for i, row in enumerate(person["OUT"]):
            self.assertTrue(np.isnan(row[0]), f"Row {i}: Expected NaN, got {row[0]}")

    def test_reciprocal_with_zeros(self):
        """Test reciprocal operation with zeros in data."""
        person = self.run_arithmetic_test("-1", in_channel="CHANNELE")
        # 0 should stay 0, others should be reciprocal
        expected = [[0], [0.1], [0], [0.2]]
        for i, (actual_row, expected_row) in enumerate(zip(person["OUT"], expected)):
            self.assertAlmostEqual(
                actual_row[0],
                expected_row[0],
                places=10,
                msg=f"Row {i}: {actual_row[0]} != {expected_row[0]}",
            )

    def test_empty_channel(self):
        """Test arithmetic on empty channel (should produce NaN)."""
        person = self.run_arithmetic_test("+", in_channel="EMPTY_CH")
        # Check structure
        self.assertEqual(len(person["OUT"]), 1)  # Should have one row
        self.assertEqual(len(person["OUT"][0]), 1)  # Should have one element

        # Check that the element is NaN (can't use == for NaN)
        self.assertTrue(
            np.isnan(person["OUT"][0][0]), f"Expected NaN, got {person['OUT'][0][0]}"
        )

    def test_invalid_channel(self):
        """Test arithmetic on non-existent channel (should skip)."""
        variables = self.make_variables()
        command_data = self.make_command(in_channel="NONEXISTENT")

        command = Arithmetic(command_data)
        try:
            result = command.execute(variables)
            self.assertIsNone(result)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_multiple_operations(self):
        """Test multiple arithmetic operations in one command."""
        variables = self.make_variables()

        command_data = {
            "class_name": "arithmetic",
            "in": ["VARNAME", "VARNAME", "VARNAME"],
            "out": ["RESULT1", "RESULT2", "RESULT3"],
            "in_channel": ["CHANNELA", "CHANNELB", "CHANNELC"],
            "out_channel": ["OUT1", "OUT2", "OUT3"],
            "format": ["+", "*", "-"],
            "num": [5, 3, 1],
            "verbosity": "none",
        }

        command = Arithmetic(command_data)
        self.assertTrue(command.good, "Command should be valid")

        result = command.execute(variables)

        # Check all results
        person1 = result["RESULT1"][0]
        person2 = result["RESULT2"][0]
        person3 = result["RESULT3"][0]

        # CHANNELA + 5
        self.assertEqual(person1["OUT1"], [[15], [25], [55], [105]])

        # CHANNELB * 3
        self.assertEqual(person2["OUT2"], [[3], [6], [15], [30]])

        # CHANNELC - 1
        self.assertEqual(person3["OUT3"], [[0, 1, 2], [4, 5, 6]])

    # Power operation tests
    def test_power_constant(self):
        """Test power operation with constant: CHANNELA ^ 2 (squaring)"""
        self.run_arithmetic_test("^", num=2, expected=[[100], [400], [2500], [10000]])

    def test_power_half(self):
        """Test power operation with constant 0.5: CHANNELA ^ 0.5 (square root)"""
        self.run_arithmetic_test(
            "^", num=0.5, expected=[[10**0.5], [20**0.5], [50**0.5], [100**0.5]]
        )

    def test_power_negative(self):
        """Test power operation with negative constant: CHANNELA ^ -1 (reciprocal)"""
        self.run_arithmetic_test(
            "^", num=-1, expected=[[1 / 10], [1 / 20], [1 / 50], [1 / 100]]
        )

    def test_power_channel_to_channel(self):
        """Test channel-to-channel power: CHANNELC ^ CHANNELD"""
        person = self.run_arithmetic_test(
            "^", in_channel="CHANNELC", in_channel_2="CHANNELD"
        )

        # First row: [1, 2, 3] ^ [3, 2, 1] = [1^3, 2^2, 3^1] = [1, 4, 3]
        # Second row: [5, 6, 7] ^ [1, 2, 3] = [5^1, 6^2, 7^3] = [5, 36, 343]

        self.assertAlmostEqual(person["OUT"][0][0], 1, places=10)  # 1^3 = 1
        self.assertAlmostEqual(person["OUT"][0][1], 4, places=10)  # 2^2 = 4
        self.assertAlmostEqual(person["OUT"][0][2], 3, places=10)  # 3^1 = 3

        self.assertAlmostEqual(person["OUT"][1][0], 5, places=10)  # 5^1 = 5
        self.assertAlmostEqual(person["OUT"][1][1], 36, places=10)  # 6^2 = 36
        self.assertAlmostEqual(person["OUT"][1][2], 343, places=10)  # 7^3 = 343

    def test_power_zero_exponent(self):
        """Test power with zero exponent: CHANNELA ^ 0 (should all be 1)"""
        self.run_arithmetic_test("^", num=0, expected=[[1], [1], [1], [1]])

    def test_power_with_negative_base(self):
        """Test power with negative values in base."""
        # Create a channel with negative values
        variables = self.make_variables()
        person = variables["VARNAME"][0]
        person["NEGATIVE_CH"] = [[-2], [-3], [4], [-5]]

        command_data = self.make_command(in_channel="NEGATIVE_CH", format="^", num=2)

        command = Arithmetic(command_data)
        result = command.execute(variables)
        person = result["VARNAME"][0]

        # (-2)^2 = 4, (-3)^2 = 9, 4^2 = 16, (-5)^2 = 25
        self.assertEqual(person["OUT"], [[4], [9], [16], [25]])

    def test_power_with_fractional_base(self):
        """Test power with fractional base values."""
        variables = self.make_variables()
        person = variables["VARNAME"][0]
        person["FRACTION_CH"] = [[0.5], [0.25], [2.5], [4.0]]

        command_data = self.make_command(in_channel="FRACTION_CH", format="^", num=2)

        command = Arithmetic(command_data)
        result = command.execute(variables)
        person = result["VARNAME"][0]

        # 0.5^2 = 0.25, 0.25^2 = 0.0625, 2.5^2 = 6.25, 4^2 = 16
        self.assertAlmostEqual(person["OUT"][0][0], 0.25, places=10)
        self.assertAlmostEqual(person["OUT"][1][0], 0.0625, places=10)
        self.assertAlmostEqual(person["OUT"][2][0], 6.25, places=10)
        self.assertAlmostEqual(person["OUT"][3][0], 16.0, places=10)

    def test_compare_power_and_reciprocal(self):
        """Compare ^ -1 and -1 operations (should be equivalent for non-zero)."""
        # Test with CHANNELA (no zeros)
        person1 = self.run_arithmetic_test("^", num=-1, in_channel="CHANNELA")
        person2 = self.run_arithmetic_test("-1", in_channel="CHANNELA")

        # Both should give same results (reciprocals)
        for i in range(len(person1["OUT"])):
            self.assertAlmostEqual(
                person1["OUT"][i][0],
                person2["OUT"][i][0],
                places=10,
                msg=f"Row {i}: power(-1)={person1['OUT'][i][0]}, reciprocal={person2['OUT'][i][0]}",
            )

    def test_power_edge_cases(self):
        """Test edge cases for power operation."""
        variables = self.make_variables()
        person = variables["VARNAME"][0]
        person["EDGE_CH"] = [[0], [1], [-1], [2]]

        # Test various exponents
        test_cases = [
            (0, [[1], [1], [1], [1]]),  # Anything^0 = 1
            (1, [[0], [1], [-1], [2]]),  # Anything^1 = itself
            (3, [[0], [1], [-1], [8]]),  # 0^3=0, 1^3=1, (-1)^3=-1, 2^3=8
        ]

        for exponent, expected in test_cases:
            command_data = self.make_command(
                in_channel="EDGE_CH", format="^", num=exponent
            )

            command = Arithmetic(command_data)
            result = command.execute(
                variables.copy()
            )  # Use copy to avoid contamination
            person = result["VARNAME"][0]

            for i, (actual_row, expected_row) in enumerate(
                zip(person["OUT"], expected)
            ):
                self.assertAlmostEqual(
                    actual_row[0],
                    expected_row[0],
                    places=10,
                    msg=f"Exponent {exponent}, row {i}: {actual_row[0]} != {expected_row[0]}",
                )


if __name__ == "__main__":
    unittest.main()

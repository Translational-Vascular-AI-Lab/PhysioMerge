import unittest
import numpy as np
from normalize import Normalize  # Adjust import path as needed


class NormalizeTest(unittest.TestCase):
    def make_variables(self):
        """Create test variables with sine wave data."""
        variables = {}
        people = []

        # Create a sine wave with amplitude 5
        n_samples = 100
        t = np.arange(n_samples) / 10.0  # 10 seconds
        amplitude = 5.0
        sine_wave = amplitude * np.sin(2 * np.pi * 1.0 * t)  # 1 Hz sine wave

        # Group into segments
        segments = [
            sine_wave[0:25].tolist(),  # First quarter
            sine_wave[25:50].tolist(),  # Second quarter
            sine_wave[50:75].tolist(),  # Third quarter
            sine_wave[75:100].tolist(),  # Fourth quarter
        ]

        person = {
            "FREQUENCY": 10,
            "FILENAME": "sine_wave_test",
            "SINE_WAVE": segments,
            "CONSTANT_WAVE": [[1.0, 1.0, 1.0, 1.0], [2.0, 2.0, 2.0, 2.0]],
        }

        people.append(person)
        variables["SINE_DATA"] = people
        return variables

    def make_command(self, **kwargs):
        """Create a command dictionary with overridable defaults."""
        command_data = {
            "class_name": "normalize",
            "in": "SINE_DATA",
            "out": "NORMALIZED_DATA",
            "in_channel": "SINE_WAVE",
            "out_channel": "NORMALIZED",
            "height": 1,
            "shift": 0,
            "verbosity": "none",
        }
        command_data.update(kwargs)
        return command_data

    def test_normalize_0_to_1(self):
        """Test normalization to range [0, 1]."""
        variables = self.make_variables()
        command_data = self.make_command(height=1, shift=0)

        command = Normalize(command_data)
        result = command.execute(variables)
        person = result["NORMALIZED_DATA"][0]
        normalized_segments = person["NORMALIZED"]

        original_segments = variables["SINE_DATA"][0]["SINE_WAVE"]

        # Check each segment
        for orig_seg, norm_seg in zip(original_segments, normalized_segments):
            seg_min = min(orig_seg)
            seg_max = max(orig_seg)

            for orig_val, norm_val in zip(orig_seg, norm_seg):
                if seg_max == seg_min:
                    expected = float(orig_val)
                else:
                    expected = 1.0 * (orig_val - seg_min) / (seg_max - seg_min) + 0.0

                self.assertAlmostEqual(norm_val, expected, delta=0.1)

            # Check bounds
            self.assertGreaterEqual(min(norm_seg), 0.0)
            self.assertLessEqual(max(norm_seg), 1.0)

    def test_normalize_0_to_10(self):
        """Test normalization to range [0, 10]."""
        variables = self.make_variables()
        command_data = self.make_command(height=10, shift=0)

        command = Normalize(command_data)
        result = command.execute(variables)
        person = result["NORMALIZED_DATA"][0]
        normalized_segments = person["NORMALIZED"]

        original_segments = variables["SINE_DATA"][0]["SINE_WAVE"]

        for orig_seg, norm_seg in zip(original_segments, normalized_segments):
            seg_min = min(orig_seg)
            seg_max = max(orig_seg)

            for orig_val, norm_val in zip(orig_seg, norm_seg):
                if seg_max == seg_min:
                    expected = float(orig_val)
                else:
                    expected = 10.0 * (orig_val - seg_min) / (seg_max - seg_min) + 0.0

                self.assertAlmostEqual(norm_val, expected, delta=0.1)

            self.assertGreaterEqual(min(norm_seg), 0.0)
            self.assertLessEqual(max(norm_seg), 10.0)

    def test_normalize_minus10_to_10(self):
        """Test normalization to range [-10, 10]."""
        variables = self.make_variables()
        command_data = self.make_command(height=20, shift=-10)

        command = Normalize(command_data)
        result = command.execute(variables)
        person = result["NORMALIZED_DATA"][0]
        normalized_segments = person["NORMALIZED"]

        original_segments = variables["SINE_DATA"][0]["SINE_WAVE"]

        for orig_seg, norm_seg in zip(original_segments, normalized_segments):
            seg_min = min(orig_seg)
            seg_max = max(orig_seg)

            for orig_val, norm_val in zip(orig_seg, norm_seg):
                if seg_max == seg_min:
                    expected = float(orig_val)
                else:
                    expected = 20.0 * (orig_val - seg_min) / (seg_max - seg_min) - 10.0

                self.assertAlmostEqual(norm_val, expected, delta=0.1)

            self.assertGreaterEqual(min(norm_seg), -10.0)
            self.assertLessEqual(max(norm_seg), 10.0)

    def test_normalize_minus1_to_0(self):
        """Test normalization to range [-1, 0]."""
        variables = self.make_variables()
        command_data = self.make_command(height=1, shift=-1)

        command = Normalize(command_data)
        result = command.execute(variables)
        person = result["NORMALIZED_DATA"][0]
        normalized_segments = person["NORMALIZED"]

        original_segments = variables["SINE_DATA"][0]["SINE_WAVE"]

        for orig_seg, norm_seg in zip(original_segments, normalized_segments):
            # Calculate segment-specific min/max
            seg_min = min(orig_seg)
            seg_max = max(orig_seg)

            # Check each normalized value using segment's own range
            for orig_val, norm_val in zip(orig_seg, norm_seg):
                if seg_max == seg_min:
                    # Constant segment (shouldn't happen here)
                    expected = float(orig_val)
                else:
                    # Use actual formula with segment's own range
                    expected = 1.0 * (orig_val - seg_min) / (seg_max - seg_min) - 1.0

                self.assertAlmostEqual(
                    norm_val,
                    expected,
                    delta=0.1,
                    msg=f"Original: {orig_val}, Seg min: {seg_min}, Seg max: {seg_max}, "
                    f"Got: {norm_val}, Expected: {expected}",
                )

            # Check bounds for this segment
            self.assertGreaterEqual(min(norm_seg), -1.0)
            self.assertLessEqual(max(norm_seg), 0.0)

    def test_normalize_minus10_to_10(self):
        """Test normalization to range [-10, 10]."""
        variables = self.make_variables()
        command_data = self.make_command(height=20, shift=-10)

        command = Normalize(command_data)
        result = command.execute(variables)
        person = result["NORMALIZED_DATA"][0]
        normalized_segments = person["NORMALIZED"]

        original_segments = variables["SINE_DATA"][0]["SINE_WAVE"]

        for orig_seg, norm_seg in zip(original_segments, normalized_segments):
            # Calculate segment-specific min/max
            seg_min = min(orig_seg)
            seg_max = max(orig_seg)

            # Check each normalized value using segment's own range
            for orig_val, norm_val in zip(orig_seg, norm_seg):
                if seg_max == seg_min:
                    # Constant segment (shouldn't happen here)
                    expected = float(orig_val)
                else:
                    # Use actual formula with segment's own range
                    expected = 20.0 * (orig_val - seg_min) / (seg_max - seg_min) - 10.0

                self.assertAlmostEqual(
                    norm_val,
                    expected,
                    delta=0.1,
                    msg=f"Original: {orig_val}, Seg min: {seg_min}, Seg max: {seg_max}, "
                    f"Got: {norm_val}, Expected: {expected}",
                )

            # Check bounds for this segment
            self.assertGreaterEqual(min(norm_seg), -10.0)
            self.assertLessEqual(max(norm_seg), 10.0)

    def test_constant_segment(self):
        """Test normalization of constant-valued segments."""
        variables = self.make_variables()
        command_data = self.make_command(
            in_channel=["CONSTANT_WAVE"],
            out_channel=["NORMALIZED_CONSTANT"],
            height=1,
            shift=0,
        )

        command = Normalize(command_data)
        result = command.execute(variables)
        person = result["NORMALIZED_DATA"][0]

        # Constant segments should remain unchanged (max == min case)
        normalized_segments = person["NORMALIZED_CONSTANT"]
        original_segments = variables["SINE_DATA"][0]["CONSTANT_WAVE"]

        for orig_seg, norm_seg in zip(original_segments, normalized_segments):
            # All values should be the same as original (converted to float)
            self.assertEqual(norm_seg, [float(val) for val in orig_seg])

    def test_multiple_operations(self):
        """Test multiple normalization operations in one command."""
        variables = self.make_variables()
        command_data = {
            "class_name": "normalize",
            "in": ["SINE_DATA", "SINE_DATA"],
            "out": ["OUT1", "OUT2"],
            "in_channel": ["SINE_WAVE", "SINE_WAVE"],
            "out_channel": ["NORM_0_1", "NORM_M1_1"],
            "height": [1, 2],
            "shift": [0, -1],
            "verbosity": "none",
        }

        command = Normalize(command_data)

        result = command.execute(variables)
        self.assertTrue(command.good, "Command should be valid")

        original_segments = variables["SINE_DATA"][0]["SINE_WAVE"]

        # Check first operation: [0, 1]
        person1 = result["OUT1"][0]
        norm1 = person1["NORM_0_1"]
        for orig_seg, norm_seg in zip(original_segments, norm1):
            seg_min = min(orig_seg)
            seg_max = max(orig_seg)

            for orig_val, norm_val in zip(orig_seg, norm_seg):
                if seg_max == seg_min:
                    expected = float(orig_val)
                else:
                    expected = 1.0 * (orig_val - seg_min) / (seg_max - seg_min) + 0.0

                self.assertAlmostEqual(norm_val, expected, delta=0.1)

            self.assertGreaterEqual(min(norm_seg), 0.0)
            self.assertLessEqual(max(norm_seg), 1.0)

        # Check second operation: [-1, 1]
        person2 = result["OUT2"][0]
        norm2 = person2["NORM_M1_1"]
        for orig_seg, norm_seg in zip(original_segments, norm2):
            seg_min = min(orig_seg)
            seg_max = max(orig_seg)

            for orig_val, norm_val in zip(orig_seg, norm_seg):
                if seg_max == seg_min:
                    expected = float(orig_val)
                else:
                    expected = 2.0 * (orig_val - seg_min) / (seg_max - seg_min) - 1.0

                self.assertAlmostEqual(norm_val, expected, delta=0.1)

            self.assertGreaterEqual(min(norm_seg), -1.0)
            self.assertLessEqual(max(norm_seg), 1.0)

    def test_invalid_parameters(self):
        """Test that invalid parameters fail validation."""
        # Test with string instead of number for height
        command_data = self.make_command(height="not_a_number")

        command = Normalize(command_data)
        # Should fail validation
        self.assertFalse(command.good)

        # Execute should return variables unchanged
        variables = self.make_variables()
        try:
            result = command.execute(variables)
            self.assertIsNone(result)
        except ValueError as e:
            self.assertIsNotNone(e)


if __name__ == "__main__":
    unittest.main()

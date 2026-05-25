import unittest
import numpy as np
from scipy.signal import find_peaks

from find_wave import FindWave


class FindWaveTest(unittest.TestCase):
    def make_variables(self):
        """Create test variables with superpositioned sine waves."""
        variables = {}
        people = []

        # Create a superposition of sine waves: 2 Hz + 5 Hz + 10 Hz
        fs = 100  # Sampling frequency
        duration = 2  # seconds
        n_samples = fs * duration
        t = np.arange(n_samples) / fs

        # Create complex signal with multiple peaks
        signal = (
            2.0 * np.sin(2 * np.pi * 2 * t)  # 2 Hz, amplitude 2
            + 1.5 * np.sin(2 * np.pi * 5 * t)  # 5 Hz, amplitude 1.5
            + 0.8 * np.sin(2 * np.pi * 10 * t)  # 10 Hz, amplitude 0.8
        )

        # Add some noise to make it more realistic
        np.random.seed(42)  # For reproducible tests
        noise = 0.1 * np.random.randn(n_samples)
        signal += noise

        person = {
            "FREQUENCY": fs,
            "FILENAME": "test_signal",
            "DATA": signal.reshape(-1, 1),  # Single channel
            "COLUMNS": ["SIGNAL"],
            "MARKERS": [[] for _ in range(n_samples)],
        }

        people.append(person)
        variables["TEST_DATA"] = people
        return variables

    def make_command(self, **kwargs):
        """Create a command dictionary with overridable defaults."""
        command_data = {
            "class_name": "findwave",
            "in": ["TEST_DATA"],
            "out": ["TEST_DATA"],
            "in_channel": ["SIGNAL"],
            "difference": "10ms",
            "prominence": 0.5,
            "height": 0,
            "format": "MAX",
            "verbosity": "none",
        }
        command_data.update(kwargs)
        return command_data

    def count_markers(self, person, channel_name):
        """Count markers for a specific channel."""
        column_idx = person["COLUMNS"].index(channel_name)
        count = 0
        for markers in person["MARKERS"]:
            if column_idx in markers:
                count += 1
        return count

    def get_marker_positions(self, person, channel_name):
        """Get positions of markers for a specific channel."""
        column_idx = person["COLUMNS"].index(channel_name)
        positions = []
        for i, markers in enumerate(person["MARKERS"]):
            if column_idx in markers:
                positions.append(i)
        return positions

    def test_prominence_only(self):
        """Test peak detection with prominence constraint only."""
        variables = self.make_variables()
        signal = variables["TEST_DATA"][0]["DATA"][:, 0]

        # Get expected peaks using scipy directly
        expected_peaks, _ = find_peaks(signal, prominence=0.5)

        command_data = self.make_command(
            prominence=0.5,
            difference="0ms",  # No distance constraint
            height=0,  # No height constraint
        )

        command = FindWave(command_data)
        self.assertTrue(command.good, "Command should be valid")

        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        # Get detected marker positions
        detected_positions = self.get_marker_positions(person, "SIGNAL")

        # Check number of peaks matches
        self.assertEqual(
            len(detected_positions),
            len(expected_peaks),
            f"Expected {len(expected_peaks)} peaks, got {len(detected_positions)}",
        )

        # Check positions match (allowing small tolerance)
        for i, (detected, expected) in enumerate(
            zip(sorted(detected_positions), sorted(expected_peaks))
        ):
            self.assertEqual(
                detected,
                expected,
                f"Peak {i}: detected at {detected}, expected at {expected}",
            )

    def test_difference_only(self):
        """Test peak detection with distance constraint only."""
        variables = self.make_variables()
        signal = variables["TEST_DATA"][0]["DATA"][:, 0]

        # Get expected peaks - distance of 10 samples
        expected_peaks, _ = find_peaks(signal, distance=10)

        command_data = self.make_command(
            prominence=0,  # No prominence constraint
            difference="100ms",  # 100ms = 10 samples at 100Hz
            height=0,  # No height constraint
        )

        command = FindWave(command_data)
        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        detected_positions = self.get_marker_positions(person, "SIGNAL")

        # Should find fewer peaks with distance constraint
        self.assertLessEqual(
            len(detected_positions),
            len(expected_peaks),
            "Distance constraint should reduce number of peaks",
        )

        # Verify minimum distance between peaks
        if len(detected_positions) > 1:
            differences = np.diff(sorted(detected_positions))
            self.assertTrue(
                np.all(differences >= 10),
                f"Peaks too close: {differences[differences < 10]}",
            )

    def test_height_only(self):
        """Test peak detection with height constraint only."""
        variables = self.make_variables()
        signal = variables["TEST_DATA"][0]["DATA"][:, 0]

        # Get expected peaks with height > 1.0
        expected_peaks, _ = find_peaks(signal, height=1.0)

        command_data = self.make_command(
            prominence=0,  # No prominence constraint
            difference="0ms",  # No distance constraint
            height=1.0,
        )

        command = FindWave(command_data)
        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        detected_positions = self.get_marker_positions(person, "SIGNAL")

        # Check number of peaks matches
        self.assertEqual(len(detected_positions), len(expected_peaks))

        # Verify all detected peaks have height >= 1.0
        for pos in detected_positions:
            self.assertGreaterEqual(
                signal[pos],
                1.0,
                f"Peak at {pos} has height {signal[pos]}, expected >= 1.0",
            )

    def test_prominence_and_difference(self):
        """Test peak detection with both prominence and distance constraints."""
        variables = self.make_variables()
        signal = variables["TEST_DATA"][0]["DATA"][:, 0]

        # Get expected peaks with both constraints
        expected_peaks, _ = find_peaks(signal, prominence=0.5, distance=10)

        command_data = self.make_command(
            prominence=0.5,
            difference="100ms",  # 100ms = 10 samples at 100Hz
            height=0,
        )

        command = FindWave(command_data)
        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        detected_positions = self.get_marker_positions(person, "SIGNAL")

        # Check number of peaks matches
        self.assertEqual(len(detected_positions), len(expected_peaks))

        # Verify constraints
        if len(detected_positions) > 1:
            differences = np.diff(sorted(detected_positions))
            self.assertTrue(
                np.all(differences >= 10), "Minimum distance constraint violated"
            )

    def test_prominence_and_height(self):
        """Test peak detection with both prominence and height constraints."""
        variables = self.make_variables()
        signal = variables["TEST_DATA"][0]["DATA"][:, 0]

        # Get expected peaks with both constraints
        expected_peaks, _ = find_peaks(signal, prominence=0.5, height=1.0)

        command_data = self.make_command(
            prominence=0.5,
            difference="0ms",
            height=1.0,
        )

        command = FindWave(command_data)
        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        detected_positions = self.get_marker_positions(person, "SIGNAL")

        # Check number of peaks matches
        self.assertEqual(len(detected_positions), len(expected_peaks))

        # Verify constraints
        for pos in detected_positions:
            self.assertGreaterEqual(
                signal[pos], 1.0, f"Height constraint violated at position {pos}"
            )

    def test_difference_and_height(self):
        """Test peak detection with both distance and height constraints."""
        variables = self.make_variables()
        signal = variables["TEST_DATA"][0]["DATA"][:, 0]

        # Get expected peaks with both constraints
        expected_peaks, _ = find_peaks(signal, distance=10, height=1.0)

        command_data = self.make_command(
            prominence=0,
            difference="100ms",  # 100ms = 10 samples at 100Hz
            height=1.0,
        )

        command = FindWave(command_data)
        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        detected_positions = self.get_marker_positions(person, "SIGNAL")

        # Check number of peaks matches
        self.assertEqual(len(detected_positions), len(expected_peaks))

        # Verify constraints
        if len(detected_positions) > 1:
            differences = np.diff(sorted(detected_positions))
            self.assertTrue(
                np.all(differences >= 10), "Minimum distance constraint violated"
            )

        for pos in detected_positions:
            self.assertGreaterEqual(
                signal[pos], 1.0, f"Height constraint violated at position {pos}"
            )

    def test_all_three_constraints(self):
        """Test peak detection with all three constraints."""
        variables = self.make_variables()
        signal = variables["TEST_DATA"][0]["DATA"][:, 0]

        # Get expected peaks with all constraints
        expected_peaks, _ = find_peaks(signal, prominence=0.5, distance=10, height=1.0)

        command_data = self.make_command(
            prominence=0.5,
            difference="100ms",  # 100ms = 10 samples at 100Hz
            height=1.0,
        )

        command = FindWave(command_data)
        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        detected_positions = self.get_marker_positions(person, "SIGNAL")

        # Check number of peaks matches
        self.assertEqual(len(detected_positions), len(expected_peaks))

        # Verify all constraints
        if len(detected_positions) > 1:
            differences = np.diff(sorted(detected_positions))
            self.assertTrue(
                np.all(differences >= 10), "Minimum distance constraint violated"
            )

        for pos in detected_positions:
            self.assertGreaterEqual(
                signal[pos], 1.0, f"Height constraint violated at position {pos}"
            )

    def test_min_detection(self):
        """Test valley (minimum) detection."""
        variables = self.make_variables()
        signal = variables["TEST_DATA"][0]["DATA"][:, 0]

        # Get expected valleys (negative peaks)
        expected_valleys, _ = find_peaks(-signal, prominence=0.5)

        command_data = self.make_command(
            format="MIN",
            prominence=0.5,
            difference="0ms",
            height=0,
        )

        command = FindWave(command_data)
        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        detected_positions = self.get_marker_positions(person, "SIGNAL")

        # Check number of valleys matches
        self.assertEqual(len(detected_positions), len(expected_valleys))

        # Verify positions match
        for i, (detected, expected) in enumerate(
            zip(sorted(detected_positions), sorted(expected_valleys))
        ):
            self.assertEqual(
                detected,
                expected,
                f"Valley {i}: detected at {detected}, expected at {expected}",
            )

    def test_time_string_conversion(self):
        """Test different time string formats."""
        variables = self.make_variables()

        # Test various time string formats
        time_tests = [
            ("100ms", 10),  # 100ms = 10 samples at 100Hz
            ("0.1s", 10),  # 0.1s = 10 samples at 100Hz
            ("0.05s", 5),  # 0.05s = 5 samples at 100Hz
            ("1s", 100),  # 1s = 100 samples at 100Hz
        ]

        for time_str, expected_samples in time_tests:
            command_data = self.make_command(
                difference=time_str,
                prominence=0.5,
            )

            command = FindWave(command_data)
            self.assertTrue(
                command.good, f"Command should be valid with time string '{time_str}'"
            )

            result = command.execute(variables.copy())
            person = result["TEST_DATA"][0]
            detected_positions = self.get_marker_positions(person, "SIGNAL")

            # Check minimum distance
            if len(detected_positions) > 1:
                differences = np.diff(sorted(detected_positions))
                self.assertTrue(
                    np.all(differences >= expected_samples),
                    f"Time string '{time_str}': peaks too close",
                )

    def test_invalid_time_string(self):
        """Test with invalid time string (should use default)."""
        variables = self.make_variables()

        command_data = self.make_command(
            difference="invalid",  # Invalid time string
            prominence=0.5,
        )

        command = FindWave(command_data)
        # Should still be valid (uses default)
        self.assertTrue(command.good)

        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        # Should still find some peaks
        detected_positions = self.get_marker_positions(person, "SIGNAL")
        self.assertGreater(len(detected_positions), 0)

    def test_zero_prominence(self):
        """Test with zero prominence (should find many peaks)."""
        variables = self.make_variables()
        signal = variables["TEST_DATA"][0]["DATA"][:, 0]

        # Get all peaks with no prominence constraint
        expected_peaks, _ = find_peaks(signal, prominence=0)

        command_data = self.make_command(
            prominence=0,
            difference="0ms",
            height=0,
        )

        command = FindWave(command_data)
        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        detected_positions = self.get_marker_positions(person, "SIGNAL")

        # Should find many peaks
        self.assertGreater(len(detected_positions), 10)
        self.assertEqual(len(detected_positions), len(expected_peaks))

    def test_very_strict_constraints(self):
        """Test with very strict constraints (should find few or no peaks)."""
        variables = self.make_variables()

        command_data = self.make_command(
            prominence=10.0,  # Very high prominence
            height=10.0,  # Very high height
            difference="10ms",
        )

        command = FindWave(command_data)
        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        detected_positions = self.get_marker_positions(person, "SIGNAL")

        # Should find few or no peaks with such strict constraints
        self.assertLessEqual(len(detected_positions), 2)

    def test_nonexistent_channel(self):
        """Test with non-existent channel (should skip)."""
        variables = self.make_variables()

        command_data = self.make_command(
            channel=["NONEXISTENT"],
            prominence=0.5,
        )

        command = FindWave(command_data)
        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        # Should not crash, just skip
        self.assertIn("MARKERS", person)

    def test_clears_existing_markers(self):
        """Test that existing markers for the channel are cleared."""
        variables = self.make_variables()
        person = variables["TEST_DATA"][0]

        # Add some existing markers for the SIGNAL channel (column 0)
        column_idx = person["COLUMNS"].index("SIGNAL")
        person["MARKERS"][50].append(column_idx)
        person["MARKERS"][100].append(column_idx)

        command_data = self.make_command(prominence=0.5)
        command = FindWave(command_data)
        result = command.execute(variables)
        person = result["TEST_DATA"][0]

        # Count markers - should only have newly detected ones
        detected_positions = self.get_marker_positions(person, "SIGNAL")

        # Old markers at 50 and 100 should be gone
        self.assertNotIn(50, detected_positions)
        self.assertNotIn(100, detected_positions)

        # Should have new markers based on actual peaks
        self.assertGreater(len(detected_positions), 0)

    def test_multiple_operations(self):
        """Test multiple findwave operations in one command."""
        # Create data with two channels
        variables = {}
        people = []

        fs = 100
        n_samples = 200
        t = np.arange(n_samples) / fs

        # Create two different signals
        signal1 = np.sin(2 * np.pi * 2 * t)
        signal2 = np.cos(2 * np.pi * 3 * t)

        person = {
            "FREQUENCY": fs,
            "FILENAME": "multi_channel_test",
            "DATA": np.column_stack([signal1, signal2]),
            "COLUMNS": ["CH1", "CH2"],
            "MARKERS": [[] for _ in range(n_samples)],
        }

        people.append(person)
        variables["MULTI_DATA"] = people

        command_data = {
            "class_name": "findwave",
            "in": ["MULTI_DATA", "MULTI_DATA"],
            "out": ["RESULT1", "RESULT2"],
            "in_channel": ["CH1", "CH2"],
            "difference": ["50ms", "30ms"],
            "prominence": [0.5, 0.3],
            "height": [0, 0],
            "format": ["MAX", "MAX"],
        }

        command = FindWave(command_data)
        self.assertTrue(command.good)

        result = command.execute(variables)

        # Check both results
        person1 = result["RESULT1"][0]
        person2 = result["RESULT2"][0]

        peaks1 = self.get_marker_positions(person1, "CH1")
        peaks2 = self.get_marker_positions(person2, "CH2")

        # Should find peaks in both channels
        self.assertGreater(len(peaks1), 0)
        self.assertGreater(len(peaks2), 0)


if __name__ == "__main__":
    unittest.main()

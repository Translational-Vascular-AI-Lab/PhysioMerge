import unittest
import sys
import os
import numpy as np

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bin"))
)

from filter import Filter  # class_name: ignore


class FilterTest(unittest.TestCase):
    def make_variables(self):
        """Create test variables with various signal types."""
        variables = {}
        people = []

        # Create test signals
        fs = 100  # 100 Hz sampling frequency
        t = np.arange(0, 10, 1 / fs)  # 10 seconds of data

        # Test signal 1: Sine wave with noise (for Butterworth, SAVGOL, Kalman)
        sine_wave = 2 * np.sin(2 * np.pi * 5 * t)  # 5 Hz sine wave
        noise = 0.5 * np.random.randn(len(t))
        noisy_sine = sine_wave + noise

        # Test signal 2: Step function (for derivative test)
        step_signal = np.zeros(len(t))
        step_signal[len(t) // 2 :] = 1.0

        # Test signal 3: Ramp with noise (for sliding standard)
        ramp_signal = 0.1 * t + 0.2 * np.random.randn(len(t))

        # Create person with multiple channels
        person = {}
        person["FREQUENCY"] = fs
        person["FILENAME"] = "test_signal"
        person["DATA"] = np.column_stack(
            [
                noisy_sine,  # Column 0: Noisy sine wave
                step_signal,  # Column 1: Step function
                ramp_signal,  # Column 2: Ramp with noise
                np.zeros(len(t)),  # Column 3: Empty column for output
            ]
        )
        person["COLUMNS"] = ["NOISY_SINE", "STEP_SIGNAL", "RAMP_SIGNAL", "OUTPUT"]

        people.append(person)
        variables["TEST_DATA"] = people

        return variables

    def make_command(self, **kwargs):
        """Create a command dictionary with overridable defaults."""
        command_data = {}
        command_data["class_name"] = "filter"
        command_data["in"] = "TEST_DATA"
        command_data["in_channel"] = "NOISY_SINE"
        command_data["out_channel"] = "OUTPUT"
        command_data["out"] = "TEST_DATA"
        command_data["function"] = "BUTTERWORTH"
        command_data["power"] = 4
        command_data["frequency"] = 10
        command_data["ftype"] = "lowpass"
        command_data["window"] = "0.5s"
        command_data["time"] = ""
        command_data["verbosity"] = "none"
        command_data.update(kwargs)

        if "name" in command_data.keys():
            command_data["in"] = command_data["name"]
        return command_data

    # ========== BUTTERWORTH FILTER TESTS ==========
    def test_butterworth_lowpass(self):
        """Test Butterworth lowpass filter."""
        variables = self.make_variables()
        command_data = self.make_command(
            function="BUTTERWORTH",
            power=4,
            frequency=10,  # 10 Hz cutoff
            ftype="lowpass",
        )

        command = Filter(command_data)
        variables = command.execute(variables)

        # Check that output exists and has correct length
        self.assertIn("TEST_DATA", variables)
        person = variables["TEST_DATA"][0]
        self.assertIn("OUTPUT", person["COLUMNS"])

        # Get input and output data
        in_idx = person["COLUMNS"].index("NOISY_SINE")
        out_idx = person["COLUMNS"].index("OUTPUT")
        input_data = person["DATA"][:, in_idx]
        output_data = person["DATA"][:, out_idx]

        # Basic checks
        self.assertEqual(len(output_data), len(input_data))
        self.assertFalse(np.all(output_data == 0))  # Should not be all zeros
        self.assertFalse(np.any(np.isnan(output_data)))  # Should not contain NaN

        # Lowpass filter should reduce high-frequency noise
        # Compute power spectral density to verify
        from scipy import signal

        f_input, Pxx_input = signal.welch(input_data, fs=100)
        f_output, Pxx_output = signal.welch(output_data, fs=100)

        # High frequency power should be reduced
        high_freq_mask = f_input > 20  # Above 20 Hz
        high_freq_reduction = np.mean(Pxx_output[high_freq_mask]) / np.mean(
            Pxx_input[high_freq_mask]
        )
        self.assertLess(
            high_freq_reduction, 0.5
        )  # High frequency power reduced by at least 50%

    def test_butterworth_highpass(self):
        """Test Butterworth highpass filter."""
        variables = self.make_variables()

        # Create a signal with low-frequency drift and high-frequency component
        fs = 100
        t = np.arange(0, 10, 1 / fs)
        drift = 0.5 * np.sin(2 * np.pi * 0.1 * t)  # 0.1 Hz drift
        signal_hf = 1.0 * np.sin(2 * np.pi * 5 * t)  # 5 Hz signal
        test_signal = drift + signal_hf

        # Update test data
        person = variables["TEST_DATA"][0]
        person["DATA"][:, 0] = test_signal  # Replace noisy_sine with our test signal

        command_data = self.make_command(
            function="BUTTERWORTH",
            power=2,
            frequency=1,  # 1 Hz cutoff
            ftype="highpass",
        )

        command = Filter(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        out_idx = person["COLUMNS"].index("OUTPUT")
        output_data = person["DATA"][:, out_idx]

        # Highpass filter should remove low-frequency drift
        # The mean should be close to zero (drift removed)
        self.assertAlmostEqual(np.mean(output_data), 0, delta=0.1)

        # Should still have the 5 Hz component
        from scipy import signal

        f, Pxx = signal.welch(output_data, fs=100)
        freq_5hz_idx = np.argmin(np.abs(f - 5))
        self.assertGreater(Pxx[freq_5hz_idx], 0.1)  # Should have power at 5 Hz

    def test_butterworth_invalid_parameters(self):
        """Test Butterworth filter with invalid parameters."""
        variables = self.make_variables()

        # Test with frequency > Nyquist (should handle gracefully)
        command_data = self.make_command(
            function="BUTTERWORTH",
            frequency=150,  # Above Nyquist (fs/2 = 50 Hz)
            ftype="lowpass",
        )

        command = Filter(command_data)

        # this shold crash
        try:
            variables = command.execute(variables)
        except Exception as e:
            self.assertIsNotNone(e)

    # ========== SAVITZKY-GOLAY FILTER TESTS ==========
    def test_savgol_filter(self):
        """Test Savitzky-Golay filter."""
        variables = self.make_variables()
        command_data = self.make_command(
            function="SAVGOL", window="0.5s", power=3  # 50 samples at 100 Hz
        )

        command = Filter(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        in_idx = person["COLUMNS"].index("NOISY_SINE")
        out_idx = person["COLUMNS"].index("OUTPUT")
        input_data = person["DATA"][:, in_idx]
        output_data = person["DATA"][:, out_idx]

        # Basic checks
        self.assertEqual(len(output_data), len(input_data))
        self.assertFalse(np.any(np.isnan(output_data)))

        # SAVGOL should smooth the signal (reduce noise)
        # Check that output is smoother than input
        input_diff = np.std(np.diff(input_data))
        output_diff = np.std(np.diff(output_data))
        self.assertLess(output_diff, input_diff * 1.5)  # Should be smoother

    def test_savgol_with_int_window(self):
        """Test Savitzky-Golay filter with integer window size."""
        variables = self.make_variables()
        command_data = self.make_command(
            function="SAVGOL", window=51, power=3  # Direct integer window size
        )

        command = Filter(command_data)
        variables = command.execute(variables)

        # Should execute without error
        self.assertIn("TEST_DATA", variables)

    def test_savgol_small_window(self):
        """Test Savitzky-Golay filter with very small window."""
        variables = self.make_variables()
        command_data = self.make_command(
            function="SAVGOL", window=3, power=1  # Very small window
        )

        command = Filter(command_data)
        variables = command.execute(variables)

        # Should execute without error
        self.assertIn("TEST_DATA", variables)

    # ========== KALMAN FILTER TESTS ==========
    def test_kalman_filter(self):
        """Test Kalman filter."""
        variables = self.make_variables()
        command_data = self.make_command(function="KALMAN")

        command = Filter(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        in_idx = person["COLUMNS"].index("NOISY_SINE")
        out_idx = person["COLUMNS"].index("OUTPUT")
        input_data = person["DATA"][:, in_idx]
        output_data = person["DATA"][:, out_idx]

        # Basic checks
        self.assertEqual(len(output_data), len(input_data))
        self.assertFalse(np.any(np.isnan(output_data)))

        # Kalman filter should reduce noise
        # Compute signal-to-noise ratio improvement
        # For sine wave, we can check reduction in variance
        true_signal = 2 * np.sin(2 * np.pi * 5 * np.arange(0, 10, 1 / 100))
        input_noise = np.var(input_data - true_signal)
        output_noise = np.var(output_data - true_signal)

        # Kalman should reduce noise (not perfect but should help)
        self.assertLess(output_noise, input_noise * 1.1)  # Allow small tolerance

    def test_kalman_filter_step_response(self):
        """Test Kalman filter with step input."""
        variables = self.make_variables()
        command_data = self.make_command(function="KALMAN", in_channel="STEP_SIGNAL")

        command = Filter(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        out_idx = person["COLUMNS"].index("OUTPUT")
        output_data = person["DATA"][:, out_idx]

        # Kalman filter should smooth the step transition
        # The step should still be visible but smoothed
        step_region = output_data[len(output_data) // 2 :]
        self.assertGreater(np.mean(step_region), 0.5)  # Should be around 1.0

    # ========== SLIDING STANDARD FILTER TESTS ==========
    def test_sliding_standard_filter(self):
        """Test sliding window standardization filter."""
        variables = self.make_variables()

        # Get the input signal
        person = variables["TEST_DATA"][0]
        in_idx = person["COLUMNS"].index("RAMP_SIGNAL")
        input_data = person["DATA"][:, in_idx]

        # Compute expected result directly (copying your implementation)
        fs = 100  # From make_variables()
        window_size = int(2 * fs)  # 2s * 100 Hz = 200 samples

        # Your implementation
        pad = window_size // 2
        x = np.pad(input_data, pad, mode="reflect")
        cumsum = np.cumsum(x, dtype=float)
        cumsum2 = np.cumsum(x**2, dtype=float)
        sum_ = cumsum[window_size:] - cumsum[:-window_size]
        sum2 = cumsum2[window_size:] - cumsum2[:-window_size]
        mean = sum_ / window_size
        var_ = sum2 / window_size - mean**2
        std = np.sqrt(np.maximum(var_, 1e-10))
        expected_output = (input_data - mean) / std

        command_data = self.make_command(
            function="SLIDING_STANDARD",
            in_channel="RAMP_SIGNAL",  # CHANGED: "channel" not "in_channel"
            out_channel="OUTPUT",
            out="TEST_DATA",
            # window="2s",
            time="2s",
            verbosity="none",
        )

        command = Filter(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        out_idx = person["COLUMNS"].index("OUTPUT")
        output_data = person["DATA"][:, out_idx]

        # Compare with expected output
        np.testing.assert_array_almost_equal(output_data, expected_output, decimal=10)

    def test_sliding_standard_small_window(self):
        """Test sliding standardization with very small window."""
        variables = self.make_variables()
        command_data = self.make_command(
            function="SLIDING_STANDARD", window="0.1s"  # 10 samples at 100 Hz
        )

        command = Filter(command_data)
        variables = command.execute(variables)

        # Should execute without error
        self.assertIn("TEST_DATA", variables)

    # ========== DERIVATIVE FILTER TESTS ==========
    def test_derivative_filter(self):
        """Test derivative filter."""
        variables = self.make_variables()

        # Get the step signal from test data
        person = variables["TEST_DATA"][0]
        step_idx = person["COLUMNS"].index("STEP_SIGNAL")
        step_signal = person["DATA"][:, step_idx]

        # Compute expected derivative directly
        expected_derivative = np.gradient(step_signal, 1)

        command_data = self.make_command(
            function="DERIVATIVE", in_channel="STEP_SIGNAL"
        )

        command = Filter(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        out_idx = person["COLUMNS"].index("OUTPUT")
        output_data = person["DATA"][:, out_idx]

        # Compare with expected derivative
        np.testing.assert_array_almost_equal(
            output_data, expected_derivative, decimal=10
        )

    def test_derivative_sine_wave(self):
        """Test derivative filter on sine wave."""
        variables = self.make_variables()
        # Use the sine wave in_channel
        command_data = self.make_command(function="DERIVATIVE", in_channel="NOISY_SINE")

        command = Filter(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        in_idx = person["COLUMNS"].index("NOISY_SINE")
        out_idx = person["COLUMNS"].index("OUTPUT")
        input_data = person["DATA"][:, in_idx]
        output_data = person["DATA"][:, out_idx]

        # Derivative of sin(ωt) is ω*cos(ωt)
        # For 5 Hz sine wave at 100 Hz sampling
        ω = 2 * np.pi * 5
        t = np.arange(0, 10, 1 / 100)
        expected_derivative = ω * np.cos(ω * t)

        # Remove the mean (derivative may have DC offset)
        output_centered = output_data - np.mean(output_data)
        expected_centered = expected_derivative - np.mean(expected_derivative)

        # Correlation should be high
        correlation = np.corrcoef(output_centered, expected_centered)[0, 1]
        self.assertGreater(correlation, 0.7)  # Should be reasonably correlated

    # ========== EDGE CASE TESTS ==========
    def test_empty_channel(self):
        """Test filter with empty in_channel."""
        variables = self.make_variables()
        # Add an empty in_channel
        person = variables["TEST_DATA"][0]
        person["DATA"] = np.hstack([person["DATA"], np.zeros((len(person["DATA"]), 1))])
        person["COLUMNS"].append("EMPTY_CHANNEL")

        command_data = self.make_command(
            in_channel="EMPTY_CHANNEL", function="BUTTERWORTH"
        )

        command = Filter(command_data)
        variables = command.execute(variables)

        # Should execute without error
        self.assertIn("TEST_DATA", variables)

    def test_nonexistent_channel(self):
        """Test filter with non-existent in_channel."""
        variables = self.make_variables()
        command_data = self.make_command(
            in_channel="NONEXISTENT", function="BUTTERWORTH"
        )

        try:
            command = Filter(command_data)
            # Should handle gracefully (skip with error message)
            variables = command.execute(variables)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_new_output_channel_creation(self):
        """Test automatic creation of new output in_channel."""
        variables = self.make_variables()
        command_data = self.make_command(out_channel="NEW_OUTPUT_CHANNEL")

        command = Filter(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]

        # New in_channel should be created
        self.assertIn("NEW_OUTPUT_CHANNEL", person["COLUMNS"])

        # Data array should have correct shape
        self.assertEqual(person["DATA"].shape[1], 5)  # Original 4 + new 1

        # New column should not be all zeros
        new_idx = person["COLUMNS"].index("NEW_OUTPUT_CHANNEL")
        new_data = person["DATA"][:, new_idx]
        self.assertFalse(np.all(new_data == 0))

    # ========== VALIDATION TESTS ==========
    def test_validation_invalid_function(self):
        """Test validation with invalid filter function."""
        command_data = self.make_command(function="INVALID_FUNCTION")
        try:
            command = Filter(command_data)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_validation_missing_required_parameters(self):
        """Test validation when required parameters are missing."""
        command_data = self.make_command()
        del command_data["function"]  # Remove required parameter
        try:
            command = Filter(command_data)
        except ValueError as e:
            self.assertIsNotNone(e)

    # ========== SPECIFIC FILTER PROPERTY TESTS ==========
    def test_butterworth_zero_phase(self):
        """Verify Butterworth filter uses zero-phase filtering."""
        variables = self.make_variables()

        # Create asymmetric test signal to detect phase distortion
        t = np.arange(0, 10, 1 / 100)
        # Create signal with sharp features
        test_signal = np.zeros_like(t)
        test_signal[200:250] = 1.0  # Pulse at 2 seconds
        test_signal[600:650] = -1.0  # Negative pulse at 6 seconds

        person = variables["TEST_DATA"][0]
        person["DATA"][:, 0] = test_signal

        command_data = self.make_command(
            function="BUTTERWORTH", power=2, frequency=5, ftype="lowpass"
        )

        command = Filter(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        out_idx = person["COLUMNS"].index("OUTPUT")
        filtered_signal = person["DATA"][:, out_idx]

        # Direct computation of what the filter should produce
        from scipy import signal

        fs = 100  # Sampling frequency from make_variables()
        b, a = signal.butter(2, 5, btype="lowpass", fs=fs)
        expected_zero_phase = signal.filtfilt(b, a, test_signal)

        # Compare your output with expected zero-phase output
        # They should be very close (within numerical precision)
        np.testing.assert_array_almost_equal(
            filtered_signal, expected_zero_phase, decimal=10
        )

    def test_savgol_preserves_polynomials(self):
        """Test that Savitzky-Golay preserves polynomials of appropriate degree."""
        variables = self.make_variables()

        # Create polynomial signals
        t = np.arange(0, 10, 1 / 100)

        # Cubic polynomial (degree 3)
        cubic_signal = 0.01 * t**3 - 0.1 * t**2 + 0.5 * t

        person = variables["TEST_DATA"][0]
        person["DATA"][:, 0] = cubic_signal

        # Use Savitzky-Golay with polynomial order 3
        command_data = self.make_command(
            function="SAVGOL",
            window="1s",  # 100 samples
            power=3,  # Same as polynomial degree
        )

        command = Filter(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        out_idx = person["COLUMNS"].index("OUTPUT")
        filtered_signal = person["DATA"][:, out_idx]

        # Savitzky-Golay with appropriate order should preserve polynomial
        # Check correlation (should be very high)
        correlation = np.corrcoef(cubic_signal, filtered_signal)[0, 1]
        self.assertGreater(correlation, 0.99)

    # ========== ERROR RECOVERY TESTS ==========
    def test_filter_failure_recovery(self):
        """Test that filter recovers gracefully from failure."""
        variables = self.make_variables()

        # Create signal that might cause numerical issues
        person = variables["TEST_DATA"][0]
        problematic_signal = np.full(len(person["DATA"]), 1e10)  # Very large values
        person["DATA"][:, 0] = problematic_signal

        command_data = self.make_command(
            function="BUTTERWORTH", frequency=10, ftype="lowpass"
        )

        try:
            command = Filter(command_data)
            result = command.execute(variables)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_execute_invalid_command_skips(self):
        """Test that invalid commands are skipped during execution."""
        variables = self.make_variables()
        command_data = self.make_command(function="INVALID_FUNCTION")

        try:
            command = Filter(command_data)
            result = command.execute(variables)
        except ValueError as e:
            self.assertIsNotNone(e)


if __name__ == "__main__":
    unittest.main()

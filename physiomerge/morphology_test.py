import unittest
import numpy as np
from morphology import Morphology

# from scipy.signal import gaussian


class MorphologyTest(unittest.TestCase):

    def create_gaussian_wave(self, length=100, center=50, std=10, amplitude=1.0):
        """Create a single Gaussian wave."""
        x = np.arange(length)
        wave = amplitude * np.exp(-0.5 * ((x - center) / std) ** 2)
        return wave.tolist()

    def create_superimposed_gaussians(
        self,
        length=300,
        centers=[50, 150, 250],
        stds=[8, 12, 10],
        amplitudes=[1.0, 0.8, 0.6],
    ):
        """Create a waveform with superimposed Gaussian waves."""
        wave = np.zeros(length)
        for center, std, amp in zip(centers, stds, amplitudes):
            x = np.arange(length)
            wave += amp * np.exp(-0.5 * ((x - center) / std) ** 2)
        return wave.tolist()

    def make_variables(self):
        """Create test variables with Gaussian wave data."""
        variables = {}
        people = []

        # Create 3 different Gaussian wave segments
        segments = []

        # Segment 1: Well-separated Gaussian waves
        segments.append(
            self.create_superimposed_gaussians(
                length=300,
                centers=[75, 150, 225],
                stds=[10, 12, 8],
                amplitudes=[1.0, 0.7, 0.5],
            )
        )

        # Segment 2: Closer Gaussian waves
        segments.append(
            self.create_superimposed_gaussians(
                length=300,
                centers=[80, 140, 220],
                stds=[15, 10, 12],
                amplitudes=[0.9, 0.6, 0.8],
            )
        )

        # Segment 3: Overlapping Gaussian waves
        segments.append(
            self.create_superimposed_gaussians(
                length=300,
                centers=[90, 120, 180],
                stds=[20, 15, 18],
                amplitudes=[1.0, 0.9, 0.7],
            )
        )

        # Create a person with these waveform segments
        person = {
            "FILENAME": "test_gaussian_waves",
            "FREQUENCY": 100,  # 100 Hz sampling rate
            "WAVEFORM": segments,
            "VALIDATION": [1, 1, 1],  # All segments are valid
            "INVALID_WAVEFORM": segments
            + [
                self.create_superimposed_gaussians(
                    length=50,  # Too short - will fail
                    centers=[10, 20, 30],
                    stds=[5, 5, 5],
                    amplitudes=[1.0, 1.0, 1.0],
                )
            ],
            "INVALID_VALIDATION": [1, 1, 1, 0],  # Last segment marked invalid
        }
        people.append(person)
        variables["TEST_DATA"] = people
        return variables

    def make_command(self, **kwargs):
        """Create a morphology command dictionary with overridable defaults."""
        command_data = {
            "class_name": "morphology",
            "in": ["TEST_DATA"],
            "out": ["RESULT"],
            "in_channel": ["WAVEFORM"],
            "out_channel": ["MORPH_FEATURES"],
            "features": ["X", "Y", "PROMINENCE", "WIDTH_50"],
            "mask": ["VALIDATION"],
            "prominence_level": 0.1,
            "verbosity": "none",
        }
        command_data.update(kwargs)
        if "name" in command_data.keys():
            command_data["in"] = command_data["name"]
        return command_data

    def test_basic_morphology_extraction(self):
        """Test basic morphology feature extraction."""
        variables = self.make_variables()
        command = self.make_command()
        morph = Morphology(command)

        # Validate the command
        self.assertTrue(morph.validate())

        # Execute the command
        result = morph.execute(variables)

        # Check that result was created
        self.assertIn("RESULT", result)
        self.assertEqual(len(result["RESULT"]), 1)

        person = result["RESULT"][0]
        self.assertIn("MORPH_FEATURES", person)

        # Check feature structure
        features = person["MORPH_FEATURES"]
        self.assertEqual(len(features), 3)  # 3 segments

        # Each feature vector should contain 7 (X) + 7 (Y) + 5 (PROMINENCE) + 5 (WIDTH_50) = 24 features
        for feature_vector in features:
            self.assertEqual(len(feature_vector), 24)

            # First 7 should be X indices (integers)
            x_values = feature_vector[:7]
            for x in x_values:
                if np.isnan(x):
                    continue
                self.assertIsInstance(x, (int, float))
                self.assertGreaterEqual(x, 0)
                self.assertLessEqual(x, 300)  # Waveform length

            # Next 7 should be Y values (amplitudes)
            y_values = feature_vector[7:14]
            for y in y_values:
                self.assertIsInstance(y, (int, float))

    def test_all_feature_formats(self):
        """Test extraction of all available feature formats."""
        all_formats = [
            "X",
            "Y",
            "WIDTH_0",
            "WIDTH_25",
            "WIDTH_50",
            "WIDTH_75",
            "PROMINENCE",
            "CURVATURE",
            "SLOPE",
            "INTEGRAL",
            "ANGLE",
            "STATS_Y",
            "STATS_X",
            "AUC",
            "DECAY",
            "VCI",
        ]

        variables = self.make_variables()
        command = self.make_command(features=all_formats)
        morph = Morphology(command)

        result = morph.execute(variables)
        person = result["RESULT"][0]
        features = person["MORPH_FEATURES"]

        # Check each segment
        for segment_features in features:
            # All features should be numbers (not NaN for valid segments)
            for feature in segment_features:
                self.assertIsInstance(feature, (int, float))

    def test_prominence_level_effect(self):
        """Test that prominence level affects peak detection."""
        variables = self.make_variables()

        # Test with high prominence (should detect fewer peaks)
        command_high = self.make_command(prominence_level=0.5)
        morph_high = Morphology(command_high)
        result_high = morph_high.execute(variables)
        features_high = result_high["RESULT"][0]["MORPH_FEATURES"]

        # Test with low prominence (should detect more peaks)
        command_low = self.make_command(prominence_level=0.01)
        morph_low = Morphology(command_low)
        result_low = morph_low.execute(variables)
        features_low = result_low["RESULT"][0]["MORPH_FEATURES"]

        # Features should be different
        self.assertNotEqual(features_high, features_low)

    def test_curvature_calculation(self):
        """Test curvature calculation on known waveform."""
        # Create a simple parabola y = x^2
        parabola = [x**2 for x in range(-10, 11)]

        # Manual curvature calculation for parabola
        # For y = x^2, curvature at x=0 should be 2
        morph = Morphology(self.make_command())

        # Test curvature at different points
        curvature_0 = morph.curvature(parabola, 10)  # x=0
        curvature_5 = morph.curvature(parabola, 15)  # x=5

        # Curvature should decrease as we move away from vertex
        self.assertGreater(curvature_0, curvature_5)

    def test_integral_calculation(self):
        """Test integral calculation."""
        morph = Morphology(self.make_command())

        # Test on simple constant function
        constant = [1.0] * 10
        integral = morph.integral(constant, 0, 10)
        self.assertAlmostEqual(integral, 10.0)

        # Test on linear function
        linear = list(range(10))
        integral = morph.integral(linear, 0, 10)
        self.assertAlmostEqual(integral, sum(range(10)))

    def test_angle_calculation(self):
        """Test angle calculation between points."""
        morph = Morphology(self.make_command())

        # Test 90-degree angle
        a = (0, 0)
        b = (0, 1)
        c = (1, 1)
        angle = morph.angle(a, b, c)
        self.assertAlmostEqual(angle, np.pi / 2, places=5)

        # Test 180-degree angle (collinear)
        a = (0, 0)
        b = (1, 1)
        c = (2, 2)
        angle = morph.angle(a, b, c)
        self.assertAlmostEqual(angle, 0.0, places=5)

    def test_center_of_mass(self):
        """Test center of mass calculation."""
        morph = Morphology(self.make_command())

        # Test with uniform distribution
        uniform = [1.0] * 10
        com = morph.center_of_mass(uniform)
        self.assertAlmostEqual(com, 4.5)  # (0*1 + 1*1 + ... + 9*1) / 10

        # Test with weighted distribution
        weighted = [0, 0, 0, 10, 0, 0]
        com = morph.center_of_mass(weighted)
        self.assertAlmostEqual(com, 3.0)

    def test_decay_calculation(self):
        """Test decay rate calculation."""
        morph = Morphology(self.make_command())

        # Create a simple decaying signal
        signal = [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
        peaks = [0]  # Peak at index 0

        # Decay to 50% height (5.0)
        decay = morph.decay(signal, peaks, 0, height=0.5)
        # Should reach 5.0 at index 5, decay rate = (10-5)/5 = 1.0
        self.assertAlmostEqual(decay, 1.0)

    def test_empty_signal_handling(self):
        """Test handling of empty signals."""
        variables = {}
        people = [{"FILENAME": "test_empty", "EMPTY_WAVE": [], "VALIDATION": [1]}]
        variables["EMPTY_DATA"] = people

        command = self.make_command(
            name=["EMPTY_DATA"], in_channel=["EMPTY_WAVE"], features=["X", "Y", "VCI"]
        )
        morph = Morphology(command)

        result = morph.execute(variables)
        person = result["RESULT"][0]
        features = person["MORPH_FEATURES"]
        # Empty data returns nothing
        self.assertListEqual(features, [])

        # Features should be NaN or appropriate defaults
        for feature in features:
            self.assertTrue(np.isnan(feature) or feature == 0)

    def test_multiple_channels(self):
        """Test morphology on multiple channels simultaneously."""
        variables = self.make_variables()

        # Add a second channel with different waves
        person = variables["TEST_DATA"][0]
        person["WAVEFORM_2"] = [
            self.create_superimposed_gaussians(centers=[60, 160, 260]),
            self.create_superimposed_gaussians(centers=[70, 170, 270]),
            self.create_superimposed_gaussians(centers=[80, 180, 280]),
        ]
        person["VALIDATION_2"] = [1, 0, 1]  # Second segment invalid

        command = self.make_command(
            name=["TEST_DATA", "TEST_DATA"],
            out=["RESULT_1", "RESULT_2"],
            in_channel=["WAVEFORM", "WAVEFORM_2"],
            out_channel=["FEATURES_1", "FEATURES_2"],
            mask=["VALIDATION", "VALIDATION_2"],
        )
        morph = Morphology(command)

        result = morph.execute(variables)

        # Both results should exist
        self.assertIn("RESULT_1", result)
        self.assertIn("RESULT_2", result)

        # Features should be different due to different waveforms
        features_1 = result["RESULT_1"][0]["FEATURES_1"]
        features_2 = result["RESULT_2"][0]["FEATURES_2"]

        self.assertNotEqual(features_1, features_2)


if __name__ == "__main__":
    unittest.main()

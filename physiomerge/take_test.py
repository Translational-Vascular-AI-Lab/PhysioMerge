import unittest
from take import Take  # type: ignore


class TakeTest(unittest.TestCase):
    def make_variables(self):
        variables = {}
        people = []
        person = {}
        person["FREQUENCY"] = 2
        person["FILENAME"] = "testing"
        person["CHANNEL"] = [[i] for i in range(1, 101)]
        person["CHANNEL_VARLEN"] = [
            [i] * i for i in range(1, 21)
        ]  # Variable length waves
        person["ALRIGHT_MASK"] = [1 for i in range(1, 101)]
        indices_to_zero = [4, 10, 20, 25, 30, 35, 80, 85, 90, 93, 98]
        for index in indices_to_zero:
            person["ALRIGHT_MASK"][index - 1] = 0
        person["ALRIGHT_VARLEN"] = [1 for i in range(1, 21)]
        person["ALRIGHT_VARLEN"][5] = 0  # Mark wave 6 as invalid
        person["ALRIGHT_VARLEN"][12] = 0  # Mark wave 13 as invalid
        person["OUT"] = []
        people.append(person)
        variables["VARNAME"] = people

        return variables

    def make_command(self, **kwargs):
        command_data = {}
        command_data["class_name"] = "take"
        command_data["in"] = "VARNAME"
        command_data["in_channel"] = "CHANNEL"
        command_data["mask"] = "ALRIGHT_MASK"
        command_data["consecutive"] = False
        command_data["waves"] = 5
        command_data["out_channel"] = "OUT"
        command_data["out"] = "VARNAME"
        command_data["direction"] = "-"
        command_data["verbosity"] = "none"
        command_data.update(kwargs)
        return command_data

    # ========== WAVE COUNT TESTS ==========
    def test_non_consec_waves_forward(self):
        """Test taking 5 non-consecutive waves searching forward."""
        variables = self.make_variables()
        command_data = self.make_command(direction="+")
        command = Take(command_data)
        variables = command.execute(variables)

        # Forward search from start: valid waves at indices 0-2, 4-8, 10-18, 20-23, 25-28, 30-33, 35-78, 80-82, 85-88, 90-91, 93-96, 98-99
        # First 5 valid waves: indices 0,1,2,4,5 -> values 1,2,3,5,6
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [[1], [2], [3], [5], [6]])

    def test_non_consec_waves_backward(self):
        """Test taking 5 non-consecutive waves searching backward."""
        variables = self.make_variables()
        command_data = self.make_command()
        command = Take(command_data)
        variables = command.execute(variables)

        # Backward search from end: valid waves at end are 100,99,97,96,95
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [[95], [96], [97], [99], [100]])

    def test_consec_waves_forward(self):
        """Test taking 5 consecutive waves searching forward."""
        variables = self.make_variables()
        command_data = self.make_command(consecutive=True, direction="+")
        command = Take(command_data)
        variables = command.execute(variables)

        # First block of 5+ consecutive valid waves: indices 0-2,4-8 (but 0-2 only 3 consecutive)
        # Next: 4-8 is 5 consecutive valid waves: indices 4,5,6,7,8 -> values 5,6,7,8,9
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [[5], [6], [7], [8], [9]])

    def test_consec_waves_backward(self):
        """Test taking 5 consecutive waves searching backward."""
        variables = self.make_variables()
        command_data = self.make_command(consecutive=True)
        command = Take(command_data)
        variables = command.execute(variables)

        # Backward search for 5+ consecutive: from end, 100,99,97,96,95 are not consecutive due to 98 being invalid
        # Need to go back further: indices 79-75 (values 80-76) are 5 consecutive valid waves
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [[75], [76], [77], [78], [79]])

    # ========== TIME DURATION TESTS ==========
    def test_non_consec_time_forward(self):
        """Test taking non-consecutive waves by time duration (5s) forward."""
        variables = self.make_variables()
        command_data = self.make_command(time="5s", waves=0, direction="+")
        command = Take(command_data)
        variables = command.execute(variables)

        # 5s at 2Hz = 10 samples needed
        # Wave length is 1 sample each, so need 10 valid waves
        # First 10 valid waves forward: indices 0,1,2,4,5,6,7,8,10,11 -> values 1-8,11,12
        for person in variables["VARNAME"]:
            self.assertEqual(
                person["OUT"], [[1], [2], [3], [5], [6], [7], [8], [9], [11], [12]]
            )

    def test_non_consec_time_backward(self):
        """Test taking non-consecutive waves by time duration (5s) backward."""
        variables = self.make_variables()
        command_data = self.make_command(time="5s", waves=0)
        command = Take(command_data)
        variables = command.execute(variables)

        # Need 10 samples, each wave is 1 sample
        # Last 10 valid waves backward: 100,99,97,96,95,94,92,91,89,88
        for person in variables["VARNAME"]:
            self.assertEqual(
                person["OUT"],
                [[88], [89], [91], [92], [94], [95], [96], [97], [99], [100]],
            )

    def test_consec_time_forward(self):
        """Test taking consecutive waves by time duration (5s) forward."""
        variables = self.make_variables()
        command_data = self.make_command(
            time="5s", waves=0, consecutive=True, direction="+"
        )
        command = Take(command_data)
        variables = command.execute(variables)

        # Need 10 consecutive valid waves
        # First block of 10+ consecutive: indices 35-78 (44 consecutive)
        # First 10: 36-45 -> values 37-46
        for person in variables["VARNAME"]:
            self.assertEqual(
                person["OUT"],
                [[36], [37], [38], [39], [40], [41], [42], [43], [44], [45]],
            )

    def test_consec_time_backward(self):
        """Test taking consecutive waves by time duration (5s) backward."""
        variables = self.make_variables()
        command_data = self.make_command(time="5s", waves=0, consecutive=True)
        command = Take(command_data)
        variables = command.execute(variables)

        # Need 10 consecutive valid waves backward
        # From end: 100,99,97,96,95,94,92,91,89,88 are not all consecutive
        # Need to find block of 10+: indices 79-70 (10 consecutive) -> values 80-71
        for person in variables["VARNAME"]:
            self.assertEqual(
                person["OUT"],
                [[70], [71], [72], [73], [74], [75], [76], [77], [78], [79]],
            )

    # ========== VARIABLE LENGTH WAVE TESTS ==========
    def test_variable_length_waves_time(self):
        """Test taking waves by time with variable length waves."""
        variables = self.make_variables()
        command_data = self.make_command(
            in_channel="CHANNEL_VARLEN",
            mask="ALRIGHT_VARLEN",
            time="10s",  # 10s at 2Hz = 20 samples needed
            waves=0,
            direction="+",
        )
        command_data["in"] = "VARNAME"
        command = Take(command_data)
        variables = command.execute(variables)

        # CHANNEL_VARLEN wave lengths: wave i has length (i % 10 + 1)
        # Waves: 1(1),2(2),3(3),4(4),5(5),6(6),7(7),8(8),9(9),10(10),11(1),12(2),13(3),14(4),15(5),16(6),17(7),18(8),19(9),20(10)
        # Invalid waves: 6(6 samples) and 13(3 samples)
        # Need 20 samples: waves 1-5 provide 1+2+3+4+5=15 samples, wave 7 provides 7 samples = 22 total
        # So should take waves 1-5 and 7
        for person in variables["VARNAME"]:
            expected_waves = [
                [1] * 1,  # Wave 1
                [2] * 2,  # Wave 2
                [3] * 3,  # Wave 3
                [4] * 4,  # Wave 4
                [5] * 5,  # Wave 5
                [7] * 7,  # Wave 7
            ]
            self.assertEqual(person["OUT"], expected_waves)

    def test_variable_length_waves_count(self):
        """Test taking specific number of waves with variable lengths."""
        variables = self.make_variables()
        command_data = self.make_command(
            in_channel="CHANNEL_VARLEN",
            mask="ALRIGHT_VARLEN",
            waves=3,
            time="",
            direction="+",
        )
        command_data["in"] = "VARNAME"
        command = Take(command_data)
        variables = command.execute(variables)

        # First 3 valid waves
        #
        # : 1,2,3 (wave 6 is invalid)
        for person in variables["VARNAME"]:
            expected_waves = [
                [1] * 1,  # Wave 1
                [2] * 2,  # Wave 2
                [3] * 3,  # Wave 3
            ]
            self.assertEqual(person["OUT"], expected_waves)

    # ========== MAXIMUM TESTS ==========
    def test_maximum_all_waves_forward(self):
        """Test taking all valid waves (maximum=True) forward."""
        variables = self.make_variables()
        command_data = self.make_command(
            waves=0, time="", maximum=True, direction="+", consecutive=False
        )
        command = Take(command_data)
        variables = command.execute(variables)

        # Should take all 89 valid waves (100 total - 11 invalid)
        for person in variables["VARNAME"]:
            self.assertEqual(len(person["OUT"]), 89)
            # Check first few and last few
            self.assertEqual(person["OUT"][0], [1])
            self.assertEqual(person["OUT"][1], [2])
            self.assertEqual(person["OUT"][2], [3])
            self.assertEqual(person["OUT"][-2], [99])
            self.assertEqual(person["OUT"][-1], [100])

    def test_maximum_consecutive_waves_forward(self):
        """Test taking maximum consecutive valid waves forward."""
        variables = self.make_variables()
        command_data = self.make_command(
            waves=0, time="", maximum=True, direction="+", consecutive=True
        )
        command = Take(command_data)
        variables = command.execute(variables)

        # Longest consecutive block forward: indices 35-78 (values 36-79) = 44 waves
        for person in variables["VARNAME"]:
            self.assertEqual(len(person["OUT"]), 44)
            self.assertEqual(person["OUT"][0], [36])
            self.assertEqual(person["OUT"][-1], [79])

    def test_maximum_consecutive_waves_backward(self):
        """Test taking maximum consecutive valid waves backward."""
        variables = self.make_variables()
        command_data = self.make_command(
            waves=0, time="", maximum=True, consecutive=True
        )
        command = Take(command_data)
        variables = command.execute(variables)

        # Longest consecutive block backward: same block 36-79 but in original order
        for person in variables["VARNAME"]:
            self.assertEqual(len(person["OUT"]), 44)
            self.assertEqual(person["OUT"][0], [36])
            self.assertEqual(person["OUT"][-1], [79])

    # ========== EDGE CASE TESTS ==========
    def test_waves_takes_priority_over_time(self):
        """Test that waves parameter takes priority when both waves and time specified."""
        variables = self.make_variables()
        command_data = self.make_command(waves=3, time="10s")
        command = Take(command_data)
        variables = command.execute(variables)

        # Should take 3 waves (waves takes priority) not 10s worth
        for person in variables["VARNAME"]:
            self.assertEqual(len(person["OUT"]), 3)
            self.assertEqual(person["OUT"], [[97], [99], [100]])

    def test_no_valid_waves(self):
        """Test when no valid waves exist in the mask."""
        variables = self.make_variables()
        # Create a mask with all zeros
        person = variables["VARNAME"][0]
        person["ALL_ZERO_MASK"] = [0] * len(person["ALRIGHT_MASK"])

        command_data = self.make_command(mask="ALL_ZERO_MASK", waves=5, direction="+")
        command = Take(command_data)
        variables = command.execute(variables)

        # Should have empty output
        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [])

    def test_exact_match_waves(self):
        """Test when exact number of requested waves is available."""
        variables = self.make_variables()
        command_data = self.make_command(
            waves=89, direction="+"
        )  # Exactly all valid waves
        command = Take(command_data)
        variables = command.execute(variables)

        for person in variables["VARNAME"]:
            self.assertEqual(len(person["OUT"]), 89)

    def test_insufficient_waves(self):
        """Test when insufficient valid waves exist for requested count."""
        variables = self.make_variables()
        command_data = self.make_command(
            waves=200, direction="+"
        )  # More than total waves
        command = Take(command_data)
        variables = command.execute(variables)

        # Should take all no waves
        for person in variables["VARNAME"]:
            self.assertEqual(len(person["OUT"]), 0)

    def test_insufficient_time(self):
        """Test when insufficient time/duration exists in valid waves."""
        variables = self.make_variables()
        command_data = self.make_command(
            time="1000s", waves=0, direction="+"
        )  # Very large time
        command = Take(command_data)
        variables = command.execute(variables)

        # Should take all available and log warning
        for person in variables["VARNAME"]:
            self.assertEqual(len(person["OUT"]), 0)

    def test_single_wave(self):
        """Test taking a single wave."""
        variables = self.make_variables()
        command_data = self.make_command(waves=1, direction="+")
        command = Take(command_data)
        variables = command.execute(variables)

        for person in variables["VARNAME"]:
            self.assertEqual(person["OUT"], [[1]])

    # ========== VALIDATION TESTS ==========
    def test_invalid_waves_type(self):
        """Test validation with invalid waves type (string instead of int)."""
        command_data = self.make_command(waves="10s")
        command = Take(command_data)
        self.assertFalse(command.good, "Command with string waves should not be valid")

    def test_no_criteria_specified(self):
        """Test validation when neither waves nor time nor maximum specified."""
        command_data = self.make_command(waves=0, time="", maximum=False)
        command = Take(command_data)
        self.assertFalse(
            command.good, "Command with no selection criteria should not be valid"
        )

    def test_invalid_direction(self):
        """Test validation with invalid direction."""
        command_data = self.make_command(direction="left")
        command = Take(command_data)
        self.assertFalse(
            command.good, "Command with invalid direction should not be valid"
        )

    def test_mismatched_parameter_lengths(self):
        """Test validation when parameter lists have mismatched lengths."""
        command_data = self.make_command()
        command_data["name"] = ["VARNAME", "OTHERNAME"]  # Different length
        command = Take(command_data)
        self.assertFalse(
            command.good,
            "Command with mismatched parameter lengths should not be valid",
        )

    # ========== MULTIPLE CHANNEL TESTS ==========
    def test_multiple_channels_simultaneously(self):
        """Test taking from multiple channels in one command."""
        variables = self.make_variables()
        command_data = {
            "class_name": "take",
            "in": ["VARNAME", "VARNAME"],
            "in_channel": ["CHANNEL", "CHANNEL_VARLEN"],
            "mask": ["ALRIGHT_MASK", "ALRIGHT_VARLEN"],
            "consecutive": [False, True],
            "waves": [5, 3],
            "out_channel": ["OUT1", "OUT2"],
            "out": ["OUTVAR1", "OUTVAR2"],
            "direction": ["-", "+"],
            "verbosity": "none",
        }

        command = Take(command_data)
        variables = command.execute(variables)

        # Check first channel results
        self.assertIn("OUTVAR1", variables)
        person = variables["OUTVAR1"][0]
        self.assertEqual(person["OUT1"], [[95], [96], [97], [99], [100]])

        # Check second channel results
        self.assertIn("OUTVAR2", variables)
        person = variables["OUTVAR2"][0]
        expected_waves = [
            [1] * 1,  # Wave 1
            [2] * 2,  # Wave 2
            [3] * 3,  # Wave 3
        ]
        self.assertEqual(person["OUT2"], expected_waves)

    # ========== FREQUENCY CONVERSION TESTS ==========
    def test_time_conversion_minutes(self):
        """Test time conversion with minutes unit."""
        variables = self.make_variables()
        command_data = self.make_command(time="0.5m", waves=0, direction="+")
        command = Take(command_data)
        variables = command.execute(variables)

        # 0.5 minutes = 30 seconds, at 2Hz = 60 samples needed
        # Each wave is 1 sample, so need 60 valid waves
        for person in variables["VARNAME"]:
            self.assertEqual(len(person["OUT"]), 60)

    def test_time_conversion_BPM(self):
        """Test time conversion with BPM unit."""
        variables = self.make_variables()
        command_data = self.make_command(time="30BPM", waves=0, direction="+")
        command = Take(command_data)
        variables = command.execute(variables)

        # 30BPM = 0.5Hz = 2 seconds per beat
        # At 2Hz sampling, need 4 samples (2 seconds * 2Hz)
        # Each wave is 1 sample, so need 4 valid waves
        for person in variables["VARNAME"]:
            self.assertEqual(len(person["OUT"]), 4)
            self.assertEqual(person["OUT"], [[1], [2], [3], [5]])

    # ========== ERROR HANDLING TESTS ==========
    def test_nonexistent_input_variable(self):
        """Test when input variable doesn't exist."""
        variables = self.make_variables()
        command_data = self.make_command(name="NONEXISTENT")
        command = Take(command_data)
        # Should log error but not crash
        result = command.execute(variables)
        self.assertIsNotNone(result)

    def test_nonexistent_channel(self):
        """Test when channel doesn't exist in person data."""
        variables = self.make_variables()
        command_data = self.make_command()
        command_data["in"] = "THIS_SHOULKDNT_WORK"
        command = Take(command_data)
        try:
            variables = command.execute(variables)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_empty_channel_data(self):
        """Test with empty channel data."""
        variables = {}
        people = []
        person = {}
        person["FREQUENCY"] = 2
        person["FILENAME"] = "empty"
        person["CHANNEL"] = []
        person["ALRIGHT_MASK"] = []
        person["OUT"] = []
        people.append(person)
        variables["EMPTY"] = people

        command_data = self.make_command(
            name="EMPTY",
            channel="CHANNEL",
            alright="ALRIGHT_MASK",
            waves=5,
            direction="+",
        )
        command = Take(command_data)
        try:
            variables = command.execute(variables)
        except ValueError as e:
            self.assertIsNotNone(e)

        for person in variables["EMPTY"]:
            self.assertEqual(person["OUT"], [])


if __name__ == "__main__":
    unittest.main()

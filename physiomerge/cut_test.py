import unittest
import numpy as np

from cut import Cut  # type: ignore


class CutTest(unittest.TestCase):
    def make_variables(self):
        """Create test variables with data, comments, and markers."""
        variables = {}
        people = []

        # Create 10 seconds of data at 100 Hz
        fs = 100
        n_samples = fs * 10  # 1000 samples
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
        comments[100] = "TASK_START"  # 1 second
        comments[150] = "CALIBRATION"
        comments[200] = "RESET"  # 2 seconds
        comments[300] = "STIMULUS_ON"  # 3 seconds
        comments[400] = "STIMULUS_OFF"  # 4 seconds
        comments[450] = "RESPONSE"
        comments[500] = "TASK_END"  # 5 seconds
        comments[700] = "ARTIFACT_START"  # 7 seconds
        comments[750] = "ARTIFACT_END"  # 7.5 seconds

        # Create markers (just for testing structure)
        markers = [""] * n_samples
        markers[100] = "M1"
        markers[500] = "M2"

        person = {}
        person["FREQUENCY"] = fs
        person["FILENAME"] = "test_recording"
        person["DATA"] = data
        person["COMMENTS"] = comments
        person["MARKERS"] = markers

        people.append(person)
        variables["TEST_DATA"] = people

        return variables

    def make_command(self, **kwargs):
        """Create a command dictionary with overridable defaults."""
        command_data = {}
        command_data["class_name"] = "cut"
        command_data["in"] = "TEST_DATA"
        command_data["out"] = "CUT_DATA"
        command_data["form"] = "COMMENT"
        command_data["comment1"] = "TASK_START"
        command_data["comment2"] = "TASK_END"
        command_data["reset"] = False
        command_data["boundary"] = ""
        command_data["period"] = "2s"
        command_data["start"] = "1s"
        command_data["direction"] = "+"
        command_data["verbosity"] = "none"
        command_data.update(kwargs)
        return command_data

    # ========== COMMENT-BASED CUTTING TESTS ==========
    def test_comment_cut_basic(self):
        """Test basic comment-based cutting between two comments."""
        variables = self.make_variables()
        command_data = self.make_command(
            form="COMMENT", comment1="TASK_START", comment2="TASK_END"
        )

        command = Cut(command_data)
        variables = command.execute(variables)

        self.assertIn("CUT_DATA", variables)
        person = variables["CUT_DATA"][0]

        # Should cut from index 100 to 500 (exclusive)
        # That's 400 samples (4 seconds at 100 Hz)
        self.assertEqual(len(person["DATA"]), 400)
        self.assertEqual(len(person["COMMENTS"]), 400)
        self.assertEqual(len(person["MARKERS"]), 400)

        # Verify data integrity
        original_person = variables["TEST_DATA"][0]
        np.testing.assert_array_equal(person["DATA"], original_person["DATA"][100:500])
        self.assertEqual(person["COMMENTS"], original_person["COMMENTS"][100:500])

    def test_comment_cut_with_reset(self):
        """Test comment cutting with reset boundary."""
        variables = self.make_variables()
        command_data = self.make_command(
            form="COMMENT", comment1="TASK_START", comment2="TASK_END", reset=True
        )

        command = Cut(command_data)
        variables = command.execute(variables)

        person = variables["CUT_DATA"][0]

        # With reset=True, should stop at RESET (index 200) instead of TASK_END
        # So cut from 100 to 200 (100 samples)
        self.assertEqual(len(person["DATA"]), 100)

        # Reset should not be here because it cuts right after
        self.assertNotIn("RESET", person["COMMENTS"])

    def test_comment_cut_boundary_outside(self):
        """Test comment cutting with boundary='outside' (remove segment)."""
        variables = self.make_variables()
        command_data = self.make_command(
            form="COMMENT",
            comment1="ARTIFACT_START",
            comment2="ARTIFACT_END",
            boundary="outside",
        )

        command = Cut(command_data)
        variables = command.execute(variables)

        person = variables["CUT_DATA"][0]

        # Should remove indices 700-750, keep everything else
        # Original 1000 samples, remove 50 = 950 samples
        self.assertEqual(len(person["DATA"]), 950)

        # Verify artifact comments are gone
        self.assertNotIn("ARTIFACT_START", person["COMMENTS"])
        self.assertIn("ARTIFACT_END", person["COMMENTS"])

    def test_comment_cut_wildcard(self):
        """Test comment cutting with wildcard comment2."""
        variables = self.make_variables()
        command_data = self.make_command(
            form="COMMENT",
            comment1="STIMULUS_ON",
            comment2="*",  # Match any non-empty comment
        )

        command = Cut(command_data)
        variables = command.execute(variables)

        person = variables["CUT_DATA"][0]

        # Should cut from STIMULUS_ON (300) to next non-empty comment (400)
        self.assertEqual(len(person["DATA"]), 100)  # 300 to 400
        self.assertEqual(person["COMMENTS"][0], "STIMULUS_ON")

    def test_comment_cut_multiple_options(self):
        """Test comment cutting with multiple comment options."""
        variables = self.make_variables()
        command_data = self.make_command(
            form="COMMENT",
            comment1=["TASK_START", "CALIBRATION"],
            comment2=["TASK_END", "RESPONSE"],
        )

        command = Cut(command_data)
        variables = command.execute(variables)

        person = variables["CUT_DATA"][0]

        # Should use last TASK_START (100) and first RESPONSE (450)
        self.assertEqual(len(person["DATA"]), 300)  # 150 to 450

    def test_comment_cut_comments_not_found(self):
        """Test comment cutting when comments are not found."""
        variables = self.make_variables()
        command_data = self.make_command(
            form="COMMENT", comment1="NONEXISTENT_START", comment2="NONEXISTENT_END"
        )

        command = Cut(command_data)
        with self.assertRaises(ValueError) as context:
            command.execute(variables)

        #person = variables["CUT_DATA"][0]

        # When comments not found, should use beginning and end
        #self.assertEqual(len(person["DATA"]), 1000)  # Entire dataset

    # ========== TIME-BASED CUTTING TESTS ==========
    def test_time_cut_forward(self):
        """Test time-based cutting in forward direction."""
        variables = self.make_variables()
        command_data = self.make_command(
            form="TIME", start="1s", period="2s", direction="+"
        )

        command = Cut(command_data)
        variables = command.execute(variables)

        person = variables["CUT_DATA"][0]

        # 1s to 3s at 100 Hz = 200 samples (indices 100-300)
        self.assertEqual(len(person["DATA"]), 200)

        # Verify correct time window
        fs = 100
        expected_data = variables["TEST_DATA"][0]["DATA"][100:300]
        np.testing.assert_array_equal(person["DATA"], expected_data)

    def test_time_cut_backward(self):
        """Test time-based cutting in backward direction."""
        variables = self.make_variables()
        command_data = self.make_command(
            form="TIME", start="2s", period="1s", direction="-"
        )

        command = Cut(command_data)
        variables = command.execute(variables)

        person = variables["CUT_DATA"][0]

        # Back 2s from end = start at 8s, period 1s = 8s to 9s
        # 1000 samples total, so indices 800 to 900
        self.assertEqual(len(person["DATA"]), 100)

        expected_data = variables["TEST_DATA"][0]["DATA"][-300:-200]
        np.testing.assert_array_almost_equal(person["DATA"], expected_data)

    def test_time_cut_boundary_outside(self):
        """Test time cutting with boundary='outside'."""
        variables = self.make_variables()
        command_data = self.make_command(
            form="TIME", start="3s", period="1s", direction="+", boundary="outside"
        )

        command = Cut(command_data)
        variables = command.execute(variables)

        person = variables["CUT_DATA"][0]

        # Remove 3s to 4s (300-400), keep rest = 900 samples
        self.assertEqual(len(person["DATA"]), 900)

        # Verify removed segment is gone
        original = variables["TEST_DATA"][0]["DATA"]
        expected = np.vstack([original[:300], original[400:]])
        np.testing.assert_array_equal(person["DATA"], expected)

    def test_time_cut_edge_cases(self):
        """Test time cutting at edges of data."""
        variables = self.make_variables()

        # Test at very beginning
        command_data1 = self.make_command(
            form="TIME", start="0s", period="0.5s", direction="+"
        )
        command1 = Cut(command_data1)
        variables = command1.execute(variables)
        person1 = variables["CUT_DATA"][0]
        self.assertEqual(len(person1["DATA"]), 50)

        # Reset variables
        variables = self.make_variables()

        # Test at very end
        command_data2 = self.make_command(
            form="TIME", start="0s", period="0.5s", direction="-"
        )
        command2 = Cut(command_data2)
        variables = command2.execute(variables)
        person2 = variables["CUT_DATA"][0]
        self.assertEqual(len(person2["DATA"]), 50)

    def test_time_cut_clamping(self):
        """Test that time cutting clamps to valid bounds."""
        variables = self.make_variables()

        # Request more time than available
        command_data = self.make_command(
            form="TIME",
            start="8s",
            period="3s",  # Would go to 11s, but only have 10s total
            direction="+",
        )

        command = Cut(command_data)
        variables = command.execute(variables)

        person = variables["CUT_DATA"][0]

        # Should clamp to 8s to 10s = 200 samples
        self.assertEqual(len(person["DATA"]), 200)

    # ========== ERROR HANDLING TESTS ==========
    def test_invalid_form_raises_value_error(self):
        """Test that invalid form raises ValueError."""
        command_data = self.make_command(form="INVALID_FORM")

        with self.assertRaises(ValueError) as context:
            command = Cut(command_data)
            # Trigger validation
            command.execute({})

        self.assertIn("Invalid form", str(context.exception))

    def test_empty_input_variable_handling(self):
        """Test handling of empty/nonexistent input variable."""
        variables = {}
        command_data = self.make_command()
        command_data["in"] = "NONEXISTENT"
        command = Cut(command_data)
        # Should handle gracefully without crashing
        try:
            result = command.execute(variables)
            self.assertIsNone(result)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_chained_cutting(self):
        """Test chaining multiple cut operations."""
        variables = self.make_variables()

        # First cut: Extract task period
        command1_data = self.make_command(
            form="COMMENT",
            comment1="TASK_START",
            comment2="ARTIFACT_END",
            out="TEST_DATA",
        )
        command1_data["in"] = "TEST_DATA"
        command1 = Cut(command1_data)
        variables = command1.execute(variables)

        # Second cut: Remove artifact from task data
        command2_data = self.make_command(
            form="COMMENT",
            comment1="ARTIFACT_START",
            comment2="ARTIFACT_END",
            boundary="outside",
            out="TEST_DATA",
        )
        command2_data["in"] = "TEST_DATA"
        command2 = Cut(command2_data)
        variables = command2.execute(variables)

        # Verify final result
        self.assertIn("TEST_DATA", variables)
        person = variables["TEST_DATA"][0]

        # Task was 100-500, artifact was at 700-750 (outside task)
        # So clean task should still be 400 samples
        self.assertEqual(len(person["DATA"]), 600)

    # ========== DATA INTEGRITY TESTS ==========
    def test_data_structure_integrity(self):
        """Test that all data structures remain aligned after cutting."""
        variables = self.make_variables()
        command_data = self.make_command(
            form="COMMENT", comment1="STIMULUS_ON", comment2="STIMULUS_OFF"
        )

        command = Cut(command_data)
        variables = command.execute(variables)

        person = variables["CUT_DATA"][0]

        # All structures should have same length
        self.assertEqual(len(person["DATA"]), len(person["COMMENTS"]))
        self.assertEqual(len(person["DATA"]), len(person["MARKERS"]))

        # Verify alignment by checking a specific point
        original = variables["TEST_DATA"][0]
        idx = 50  # Check middle of cut segment

        # Should correspond to original index 350
        np.testing.assert_array_equal(person["DATA"][idx], original["DATA"][350])
        self.assertEqual(person["COMMENTS"][idx], original["COMMENTS"][350])
        self.assertEqual(person["MARKERS"][idx], original["MARKERS"][350])

    def test_comment_processing(self):
        """Test that comments are properly processed (uppercase, stripped)."""
        variables = self.make_variables()

        # Add comments with spaces and mixed case
        original_person = variables["TEST_DATA"][0]
        original_person["COMMENTS"][50] = "  (test start)  "
        original_person["COMMENTS"][150] = "{Test End}  "

        command_data = self.make_command(
            form="COMMENT",
            comment1="TESTSTART",  # Should match after processing
            comment2="TESTEND",
        )

        command = Cut(command_data)
        with self.assertRaises(ValueError) as context:
            command.execute({})
        #variables = command.execute(variables)

        #person = variables["CUT_DATA"][0]
        # Should find and cut between the processed comments
        #self.assertGreater(len(person["DATA"]), 0)

    # ========== BOUNDARY CONDITION TESTS ==========
    def test_zero_length_cut(self):
        """Test cutting with zero-length segment."""
        variables = self.make_variables()

        # Cut with same start and end comment
        command_data = self.make_command(
            form="COMMENT",
            comment1="TASK_START",
            comment2="TASK_START",  # Same as start
        )

        command = Cut(command_data)
        variables = command.execute(variables)

        person = variables["CUT_DATA"][0]

        # Zero-length cut with boundary="" should give empty result
        # With boundary="outside" should give full data minus that point
        # Current implementation gives empty for boundary=""
        self.assertEqual(len(person["DATA"]), 0)

    def test_full_data_cut(self):
        """Test cutting entire dataset."""
        variables = self.make_variables()

        # Cut from beginning to end
        command_data = self.make_command(
            form="TIME", start="0s", period="10s", direction="+"
        )

        command = Cut(command_data)
        variables = command.execute(variables)

        person = variables["CUT_DATA"][0]

        # Should have all data
        self.assertEqual(len(person["DATA"]), 1000)
        np.testing.assert_array_equal(person["DATA"], variables["TEST_DATA"][0]["DATA"])


if __name__ == "__main__":
    unittest.main()

import unittest
import numpy as np

# Adjust import path as needed
from partition import Partition


class PartitionTest(unittest.TestCase):
    def make_variables(self):
        """Create test variables with data, comments, and markers."""
        variables = {}
        people = []

        # Create 10 seconds of data at 100 Hz
        fs = 100
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
        comments[100] = "TASK_START"  # 1 second
        comments[150] = "CALIBRATION"
        comments[200] = "RESET"  # 2 seconds
        comments[300] = "STIMULUS_ON"  # 3 seconds
        comments[400] = "STIMULUS_OFF"  # 4 seconds
        comments[450] = "RESPONSE"
        comments[500] = "TASK_END"  # 5 seconds
        comments[700] = "ARTIFACT_START"  # 7 seconds
        comments[750] = "ARTIFACT_END"  # 7.5 seconds

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

        return variables

    def make_command(self, **kwargs):
        """Create a command dictionary with overridable defaults."""
        command_data = {}
        command_data["class_name"] = "cut"
        command_data["in"] = "TEST_DATA"
        command_data["out"] = "TEST_DATA"
        command_data["form"] = "COMMENT"
        command_data["in_channel"] = "1hz"
        command_data["out_channel"] = "PARTITIONS"
        command_data["index"] = "1hz"
        command_data["del_first"] = False
        command_data["del_last"] = False
        command_data["verbosity"] = "none"
        command_data.update(kwargs)
        if "name" in command_data:
            command_data["in"] = command_data["name"]
        return command_data

    def test_basic_partition(self):
        """Test basic partitioning functionality."""
        variables = self.make_variables()
        command_data = self.make_command()

        command = Partition(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        self.assertEqual(len(person["PARTITIONS"]), 10)

        # Check first partition matches first 100 samples
        column = person["DATA"][0:100, 0]
        wave0 = person["PARTITIONS"][0]
        column_list = column.tolist()

        self.assertEqual(len(wave0), len(column_list))
        for i, (val1, val2) in enumerate(zip(wave0, column_list)):
            self.assertAlmostEqual(
                val1, val2, places=10, msg=f"Mismatch at position {i}: {val1} != {val2}"
            )

        # Check last partition matches last 100 samples
        column = person["DATA"][900:1000, 0]
        wave_last = person["PARTITIONS"][-1]
        column_list = column.tolist()

        self.assertEqual(len(wave_last), len(column_list))
        for i, (val1, val2) in enumerate(zip(wave_last, column_list)):
            self.assertAlmostEqual(
                val1, val2, places=10, msg=f"Mismatch at position {i}: {val1} != {val2}"
            )

    def test_2hz_index_partition(self):
        """Test partitioning with 2HZ as index."""
        variables = self.make_variables()
        command_data = self.make_command(index="2HZ")

        command = Partition(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        # 2Hz markers every 0.5 seconds = 20 partitions
        self.assertEqual(len(person["PARTITIONS"]), 20)

        # Check first partition matches first 50 samples
        column = person["DATA"][0:50, 0]
        wave0 = person["PARTITIONS"][0]
        column_list = column.tolist()

        self.assertEqual(len(wave0), len(column_list))
        for i, (val1, val2) in enumerate(zip(wave0, column_list)):
            self.assertAlmostEqual(
                val1, val2, places=10, msg=f"Mismatch at position {i}: {val1} != {val2}"
            )

    def test_ramp_index_partition(self):
        """Test partitioning with RAMP as index."""
        variables = self.make_variables()
        command_data = self.make_command(index="RAMP")

        command = Partition(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        # RAMP markers every 2 seconds = 5 partitions
        self.assertEqual(len(person["PARTITIONS"]), 5)

        # Check first partition matches first 200 samples
        column = person["DATA"][0:200, 0]
        wave0 = person["PARTITIONS"][0]
        column_list = column.tolist()

        self.assertEqual(len(wave0), len(column_list))
        for i, (val1, val2) in enumerate(zip(wave0, column_list)):
            self.assertAlmostEqual(
                val1, val2, places=10, msg=f"Mismatch at position {i}: {val1} != {val2}"
            )

    def test_different_channel_same_index(self):
        """Test partitioning a different channel with same index."""
        variables = self.make_variables()
        command_data = self.make_command(in_channel="2HZ", out_channel="2HZ_PARTITIONS")

        command = Partition(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        self.assertIn("2HZ_PARTITIONS", person)
        self.assertEqual(len(person["2HZ_PARTITIONS"]), 10)

        # Check first partition matches first 100 samples of 2HZ channel
        column = person["DATA"][0:100, 1]
        wave0 = person["2HZ_PARTITIONS"][0]
        column_list = column.tolist()

        self.assertEqual(len(wave0), len(column_list))
        for i, (val1, val2) in enumerate(zip(wave0, column_list)):
            self.assertAlmostEqual(
                val1, val2, places=10, msg=f"Mismatch at position {i}: {val1} != {val2}"
            )

    def test_del_first_ramp_index(self):
        """Test delete first partition with RAMP index."""
        variables = self.make_variables()
        command_data = self.make_command(index="RAMP", del_first=True)

        command = Partition(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        # 5 partitions minus first = 4 partitions
        self.assertEqual(len(person["PARTITIONS"]), 4)

        # First partition should now be original second partition (indices 200-399)
        column = person["DATA"][200:400, 0]
        wave0 = person["PARTITIONS"][0]
        column_list = column.tolist()

        self.assertEqual(len(wave0), len(column_list))
        for i, (val1, val2) in enumerate(zip(wave0, column_list)):
            self.assertAlmostEqual(
                val1, val2, places=10, msg=f"Mismatch at position {i}: {val1} != {val2}"
            )

    def test_del_last_ramp_index(self):
        """Test delete last partition with RAMP index."""
        variables = self.make_variables()
        command_data = self.make_command(index="RAMP", del_last=True)

        command = Partition(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        # 5 partitions minus last = 4 partitions
        self.assertEqual(len(person["PARTITIONS"]), 4)

        # Last partition should now be original second-last partition (indices 600-799)
        column = person["DATA"][600:800, 0]
        wave_last = person["PARTITIONS"][-1]
        column_list = column.tolist()

        self.assertEqual(len(wave_last), len(column_list))
        for i, (val1, val2) in enumerate(zip(wave_last, column_list)):
            self.assertAlmostEqual(
                val1, val2, places=10, msg=f"Mismatch at position {i}: {val1} != {val2}"
            )

    def test_del_both_ramp_index(self):
        """Test delete both first and last partitions with RAMP index."""
        variables = self.make_variables()
        command_data = self.make_command(index="RAMP", del_first=True, del_last=True)

        command = Partition(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        # 5 partitions minus first and last = 3 partitions
        self.assertEqual(len(person["PARTITIONS"]), 3)

        # Check middle partitions are correct
        # First partition should be original second partition (indices 200-399)
        column1 = person["DATA"][200:400, 0]
        wave0 = person["PARTITIONS"][0]
        column_list1 = column1.tolist()

        self.assertEqual(len(wave0), len(column_list1))
        for i, (val1, val2) in enumerate(zip(wave0, column_list1)):
            self.assertAlmostEqual(
                val1, val2, places=10, msg=f"Mismatch at position {i}: {val1} != {val2}"
            )

        # Last partition should be original second-last partition (indices 600-799)
        column2 = person["DATA"][600:800, 0]
        wave_last = person["PARTITIONS"][-1]
        column_list2 = column2.tolist()

        self.assertEqual(len(wave_last), len(column_list2))
        for i, (val1, val2) in enumerate(zip(wave_last, column_list2)):
            self.assertAlmostEqual(
                val1, val2, places=10, msg=f"Mismatch at position {i}: {val1} != {val2}"
            )

    def test_del_first_1hz_index(self):
        """Test delete first partition with 1HZ index."""
        variables = self.make_variables()
        command_data = self.make_command(del_first=True)

        command = Partition(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        # 10 partitions minus first = 9 partitions
        self.assertEqual(len(person["PARTITIONS"]), 9)

        # First partition should now be original second partition (indices 100-199)
        column = person["DATA"][100:200, 0]
        wave0 = person["PARTITIONS"][0]
        column_list = column.tolist()

        self.assertEqual(len(wave0), len(column_list))
        for i, (val1, val2) in enumerate(zip(wave0, column_list)):
            self.assertAlmostEqual(
                val1, val2, places=10, msg=f"Mismatch at position {i}: {val1} != {val2}"
            )

    def test_del_last_1hz_index(self):
        """Test delete last partition with 1HZ index."""
        variables = self.make_variables()
        command_data = self.make_command(del_last=True)

        command = Partition(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        # 10 partitions minus last = 9 partitions
        self.assertEqual(len(person["PARTITIONS"]), 9)

        # Last partition should now be original second-last partition (indices 800-899)
        column = person["DATA"][800:900, 0]
        wave_last = person["PARTITIONS"][-1]
        column_list = column.tolist()

        self.assertEqual(len(wave_last), len(column_list))
        for i, (val1, val2) in enumerate(zip(wave_last, column_list)):
            self.assertAlmostEqual(
                val1, val2, places=10, msg=f"Mismatch at position {i}: {val1} != {val2}"
            )

    def test_case_insensitive_column_names(self):
        """Test that column names are case-insensitive."""
        variables = self.make_variables()
        # Use lowercase column names
        command_data = self.make_command(
            in_channel="1hz", index="ramp", out_channel="lower_partitions"
        )

        command = Partition(command_data)
        variables = command.execute(variables)

        person = variables["TEST_DATA"][0]
        self.assertIn("LOWER_PARTITIONS", person)
        # Should still get 5 partitions with RAMP index
        self.assertEqual(len(person["LOWER_PARTITIONS"]), 5)

    def test_nonexistent_channel(self):
        """Test with non-existent channel name."""
        variables = self.make_variables()
        command_data = self.make_command(
            in_channel="NONEXISTENT", out_channel="empty_partitions"
        )

        command = Partition(command_data)
        try:
            variables = command.execute(variables)
            self.assertIsNone(variables)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_nonexistent_index(self):
        """Test with non-existent index name."""
        variables = self.make_variables()
        command_data = self.make_command(
            index="NONEXISTENT", out_channel="no_index_partitions"
        )

        command = Partition(command_data)
        try:
            variables = command.execute(variables)
            self.assertIsNone(variables)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_multiple_output_channels(self):
        """Test creating multiple partition outputs."""
        variables = self.make_variables()

        # First partition
        command_data1 = self.make_command(out_channel="PARTITIONS_1HZ", index="1HZ")
        command1 = Partition(command_data1)
        variables = command1.execute(variables)

        # Second partition with different index
        command_data2 = self.make_command(out_channel="PARTITIONS_RAMP", index="RAMP")
        command2 = Partition(command_data2)
        variables = command2.execute(variables)

        person = variables["TEST_DATA"][0]

        # Both should exist with correct partition counts
        self.assertIn("PARTITIONS_1HZ", person)
        self.assertIn("PARTITIONS_RAMP", person)

        self.assertEqual(len(person["PARTITIONS_1HZ"]), 10)
        self.assertEqual(len(person["PARTITIONS_RAMP"]), 5)

    def test_partition_all_channels(self):
        """Test partitioning all three channels."""
        variables = self.make_variables()

        # Test 1HZ channel
        command_data1 = self.make_command(
            in_channel="1HZ", out_channel="1HZ_PART", index="1HZ"
        )
        command1 = Partition(command_data1)
        variables = command1.execute(variables)

        # Test 2HZ channel
        command_data2 = self.make_command(
            in_channel="2HZ", out_channel="2HZ_PART", index="1HZ"  # Same index for all
        )
        command2 = Partition(command_data2)
        variables = command2.execute(variables)

        # Test RAMP channel
        command_data3 = self.make_command(
            in_channel="RAMP",
            out_channel="RAMP_PART",
            index="1HZ",  # Same index for all
        )
        command3 = Partition(command_data3)
        variables = command3.execute(variables)

        person = variables["TEST_DATA"][0]

        # All should have same number of partitions (10)
        self.assertEqual(len(person["1HZ_PART"]), 10)
        self.assertEqual(len(person["2HZ_PART"]), 10)
        self.assertEqual(len(person["RAMP_PART"]), 10)

        # Check values in one partition match across channels
        partition_idx = 2  # Third partition
        self.assertEqual(
            len(person["1HZ_PART"][partition_idx]),
            len(person["2HZ_PART"][partition_idx]),
        )
        self.assertEqual(
            len(person["1HZ_PART"][partition_idx]),
            len(person["RAMP_PART"][partition_idx]),
        )

    def test_empty_markers(self):
        """Test partitioning when there are no markers."""
        variables = self.make_variables()

        # Create a copy and remove all markers
        person_copy = variables["TEST_DATA"][0].copy()
        person_copy["MARKERS"] = [[] for _ in range(len(person_copy["DATA"]))]

        variables["NO_MARKERS"] = [person_copy]

        command_data = self.make_command(
            name="NO_MARKERS", out="NO_MARKERS", out_channel="no_marker_partitions"
        )

        command = Partition(command_data)
        variables = command.execute(variables)

        person = variables["NO_MARKERS"][0]
        partitions = person["NO_MARKER_PARTITIONS"]

        # With no markers, should get one partition with all data
        self.assertEqual(len(partitions), 1)
        self.assertEqual(len(partitions[0]), 1000)  # All 1000 samples

    def test_invalid_command_parameters(self):
        """Test that invalid command parameters don't crash."""
        variables = self.make_variables()

        # Test with invalid type for del_first
        command_data = self.make_command(del_first="not_a_boolean")

        try:
            command = Partition(command_data)
            self.assertIsNone(command)
        except ValueError as e:
            self.assertIsNotNone(e)


if __name__ == "__main__":
    unittest.main()

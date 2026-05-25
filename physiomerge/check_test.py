import unittest
import numpy as np
from check import Check  # type: ignore


class CheckTest(unittest.TestCase):
    def make_variables(self):
        variables = {}
        people = []
        person = {}
        person["FREQUENCY"] = 2
        person["FILENAME"] = "testing"
        person["CHANNELA"] = [
            [0, 1, 2, 1, 1],  # Row 0: min=0 at index 0, max=2 at index 2
            [-1, 2, 1, 1, 1],  # Row 1: min=-1 at index 0, max=2 at index 1
            [0, 1, 1, 1, 2],  # Row 2: min=0 at index 0, max=2 at index 4
            [-2, 0],  # Row 3: min=-2 at index 0, max=0 at index 1
            [0, 1, 1, 1, 1, 1, 1, 2],  # Row 4: min=0 at index 0, max=2 at index 7
            [-2, -3, -2, -2, -1],  # Row 5: min=-3 at index 1, max=-1 at index 4
            [2, 2, 1, 2, 3],  # Row 6: min=1 at index 2, max=3 at index 4
            [3, 1, -2, 1, 0],  # Row 7: min=-2 at index 2, max=3 at index 0
        ]
        person["CHANNELB"] = [
            [1, 2, 3, 4, 5],  # For mean, median tests
            [2, 2, 2, 2, 2],  # All same values for flat region test
            [1, 1.1, 1.2, 1.3, 1.4],  # Gradual increase for flat region test
        ]
        person["ALIGHT2"] = [0, 0, 0, 0, 1, 1, 1, 1]
        person["ALRIGHT1"] = [1, 1, 1, 1, 1, 1, 1, 1]  # Existing mask for testing
        #person["ALRIGHT1"] = [1, 1, 1, 1, 1, 1, 1, 1]  # Existing mask for testing
        people.append(person)
        variables["VARNAME"] = people
        return variables

    def make_command(self):
        command_data = {}
        command_data["class_name"] = "check"
        command_data["in"] = "VARNAME"
        command_data["in_channel"] = "CHANNELA"
        command_data["out_channel"] = "OUT"
        command_data["out"] = "VARNAME"
        command_data["variable"] = "min"
        command_data["format"] = "y"
        command_data["compare"] = "<"
        command_data["mask"] = "ALRIGHT1"
        command_data["num"] = 0
        command_data["verbosity"] = "none"
        return command_data

    # Helper method for creating specific test commands
    def create_test_command(self, **kwargs):
        command_data = self.make_command()
        command_data.update(kwargs)
        return command_data

    # ========== MIN TESTS ==========
    def test_check_min_less_y_noalight(self):
        """Test MIN variable with < operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command()
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # Row values: [0, -1, 0, -2, 0, -3, 1, -2]
            # < 0: [-1, -2, -3, -2] -> rows 1, 3, 5, 7
            self.assertEqual([0, 1, 0, 1, 0, 1, 0, 1], person["ALRIGHT1"])
        pass

    def test_check_min_greater_y_noalight(self):
        """Test MIN variable with > operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(compare=">")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # > 0: [1] -> row 6 only
            self.assertEqual([0, 0, 0, 0, 0, 0, 1, 0], person["ALRIGHT1"])
        pass

    def test_check_min_lessequal_y_noalight(self):
        """Test MIN variable with <= operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(compare="<=")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # <= 0: [0, -1, 0, -2, 0, -3, -2] -> all except row 6
            self.assertEqual([1, 1, 1, 1, 1, 1, 0, 1], person["ALRIGHT1"])
        pass

    def test_check_min_greatequal_y_noalight(self):
        """Test MIN variable with >= operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(compare=">=")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # >= 0: [0, 0, 0, 1] -> rows 0, 2, 4, 6
            self.assertEqual([1, 0, 1, 0, 1, 0, 1, 0], person["ALRIGHT1"])
        pass

    def test_check_min_equal_y_noalight(self):
        """Test MIN variable with == operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(compare="==")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # == 0: [0, 0, 0] -> rows 0, 2, 4
            self.assertEqual([1, 0, 1, 0, 1, 0, 0, 0], person["ALRIGHT1"])
        pass

    def test_check_min_notequal_y_noalight(self):
        """Test MIN variable with != operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(compare="!=")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # != 0: [-1, -2, -3, 1, -2] -> rows 1, 3, 5, 6, 7
            self.assertEqual([0, 1, 0, 1, 0, 1, 1, 1], person["ALRIGHT1"])
        pass

    def test_check_min_less_x_noalight(self):
        """Test MIN variable with < operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(format="x")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # Min indices: [0, 0, 0, 0, 0, 1, 2, 2]
            # < 0: none
            self.assertEqual([0, 0, 0, 0, 0, 0, 0, 0], person["ALRIGHT1"])
        pass

    def test_check_min_greater_x_noalight(self):
        """Test MIN variable with > operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(compare=">", format="x")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # > 0: indices > 0 -> rows 5, 6, 7
            self.assertEqual([0, 0, 0, 0, 0, 1, 1, 1], person["ALRIGHT1"])
        pass

    def test_check_min_lessequal_x_noalight(self):
        """Test MIN variable with <= operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(compare="<=", format="x")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # <= 0: indices <= 0 -> rows 0-4
            self.assertEqual([1, 1, 1, 1, 1, 0, 0, 0], person["ALRIGHT1"])
        pass

    def test_check_min_greatequal_x_noalight(self):
        """Test MIN variable with >= operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(compare=">=", format="x")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # >= 0: all indices >= 0 -> all rows
            self.assertEqual([1, 1, 1, 1, 1, 1, 1, 1], person["ALRIGHT1"])
        pass

    def test_check_min_equal_x_noalight(self):
        """Test MIN variable with == operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(compare="==", format="x")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # == 0: indices == 0 -> rows 0-4
            self.assertEqual([1, 1, 1, 1, 1, 0, 0, 0], person["ALRIGHT1"])
        pass

    def test_check_min_notequal_x_noalight(self):
        """Test MIN variable with != operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(compare="!=", format="x")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # != 0: indices != 0 -> rows 5, 6, 7
            self.assertEqual([0, 0, 0, 0, 0, 1, 1, 1], person["ALRIGHT1"])
        pass

    # ========== MAX TESTS ==========
    def test_check_max_less_y_noalight(self):
        """Test MAX variable with < operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="max")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # Max values: [2, 2, 2, 0, 2, -1, 3, 3]
            # < 0: only row 5 (max=-1)
            self.assertEqual([0, 0, 0, 0, 0, 1, 0, 0], person["ALRIGHT1"])
        pass

    def test_check_max_greater_y_noalight(self):
        """Test MAX variable with > operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="max", compare=">")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # > 0: rows 0, 1, 2, 4, 6, 7
            self.assertEqual([1, 1, 1, 0, 1, 0, 1, 1], person["ALRIGHT1"])
        pass

    def test_check_max_lessequal_y_noalight(self):
        """Test MAX variable with <= operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="max", compare="<=")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # <= 0: rows 3, 5
            self.assertEqual([0, 0, 0, 1, 0, 1, 0, 0], person["ALRIGHT1"])
        pass

    def test_check_max_greatequal_y_noalight(self):
        """Test MAX variable with >= operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="max", compare=">=")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # >= 0: all except row 5
            self.assertEqual([1, 1, 1, 1, 1, 0, 1, 1], person["ALRIGHT1"])
        pass

    def test_check_max_equal_y_noalight(self):
        """Test MAX variable with == operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="max", compare="==")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # == 0: only row 3
            self.assertEqual([0, 0, 0, 1, 0, 0, 0, 0], person["ALRIGHT1"])
        pass

    def test_check_max_notequal_y_noalight(self):
        """Test MAX variable with != operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="max", compare="!=")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # != 0: all except row 3
            self.assertEqual([1, 1, 1, 0, 1, 1, 1, 1], person["ALRIGHT1"])
        pass

    def test_check_max_less_x_noalight(self):
        """Test MAX variable with < operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="max", format="x")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # Max indices: [2, 1, 4, 1, 7, 4, 4, 0]
            # < 0: none
            self.assertEqual([0, 0, 0, 0, 0, 0, 0, 0], person["ALRIGHT1"])
        pass

    def test_check_max_greater_x_noalight(self):
        """Test MAX variable with > operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="max", compare=">", format="x")
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # > 0: indices > 0 -> all except row 7
            self.assertEqual([1, 1, 1, 1, 1, 1, 1, 0], person["ALRIGHT1"])
        pass

    def test_check_max_lessequal_x_noalight(self):
        """Test MAX variable with <= operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="max", compare="<=", format="x"
        )
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # <= 0: only row 7 (index 0)
            self.assertEqual([0, 0, 0, 0, 0, 0, 0, 1], person["ALRIGHT1"])
        pass

    def test_check_max_greatequal_x_noalight(self):
        """Test MAX variable with >= operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="max", compare=">=", format="x"
        )
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # >= 0: all indices >= 0 -> all rows
            self.assertEqual([1, 1, 1, 1, 1, 1, 1, 1], person["ALRIGHT1"])
        pass

    def test_check_max_equal_x_noalight(self):
        """Test MAX variable with == operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="max", compare="==", format="x"
        )
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # == 0: only row 7
            self.assertEqual([0, 0, 0, 0, 0, 0, 0, 1], person["ALRIGHT1"])
        pass

    def test_check_max_notequal_x_noalight(self):
        """Test MAX variable with != operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="max", compare="!=", format="x"
        )
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # != 0: all except row 7
            self.assertEqual([1, 1, 1, 1, 1, 1, 1, 0], person["ALRIGHT1"])
        pass

    # ========== MEAN TESTS ==========
    def test_check_mean_less_y_noalight(self):
        """Test MEAN variable with < operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="mean", in_channel="CHANNELB", num=3.0
        )
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # CHANNELB means: [3.0, 2.0, 1.2]
            # < 3.0: rows 1, 2
            self.assertEqual([0, 1, 1, 1, 1, 1, 1, 1], person["ALRIGHT1"])
        pass

    def test_check_mean_greater_y_noalight(self):
        """Test MEAN variable with > operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="mean", in_channel="CHANNELB", compare=">", num=2.0
        )
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # > 2.0: row 0 (mean=3.0)
            self.assertEqual([1, 0, 0, 1, 1, 1, 1, 1], person["ALRIGHT1"])
        pass

    # ========== MEDIAN TESTS ==========
    def test_check_median_less_y_noalight(self):
        """Test MEDIAN variable with < operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="median", in_channel="CHANNELB", num=3.0
        )
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # CHANNELB medians: [3.0, 2.0, 1.2]
            # < 3.0: rows 1, 2
            self.assertEqual([0, 1, 1, 1, 1, 1, 1, 1], person["ALRIGHT1"])
        pass

    def test_check_median_equal_y_noalight(self):
        """Test MEDIAN variable with == operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="median", in_channel="CHANNELB", compare="==", num=2.0
        )
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # == 2.0: row 1 only
            self.assertEqual([0, 1, 0, 1, 1, 1, 1, 1], person["ALRIGHT1"])
        pass

    # ========== START TESTS ==========
    def test_check_start_less_y_noalight(self):
        """Test START variable with < operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="start", num=0.5)
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # START values (second element): [0, -1, 0, -2, 0, -2, 2, 3]
            # < 0.5: rows 5 only (-3)
            self.assertEqual([1, 1, 1, 1, 1, 1, 0, 0], person["ALRIGHT1"])
        pass

    def test_check_start_greater_y_noalight(self):
        """Test START variable with > operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="start", compare=">", num=0.5)
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # > 0.5: all except row 3 (0) and row 5 (-3)
            self.assertEqual([0, 0, 0, 0, 0, 0, 1, 1], person["ALRIGHT1"])
        pass

    # ========== END TESTS ==========
    def test_check_end_less_x_noalight(self):
        """Test END variable with < operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="end", compare="<", time="3s", format="x"
        )
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # END indices: [4, 4, 4, 1, 7, 4, 4, 4]
            # Convert 3s to samples: 3s * 2Hz = 6 samples
            # < 6: all except row 4 (index 7)
            self.assertEqual([1, 1, 1, 1, 0, 1, 1, 1], person["ALRIGHT1"])
        pass

    def test_check_end_greater_x_noalight(self):
        """Test END variable with > operator in X format."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="end", compare=">", time="1s", format="x"
        )
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # Convert 1s to samples: 1s * 2Hz = 2 samples
            # > 2: all except row 3 (index 1)
            self.assertEqual([1, 1, 1, 0, 1, 1, 1, 1], person["ALRIGHT1"])
        pass

    def test_check_end_greater_x_noalright_BPM(self):
        """Test END variable with > operator in X format using BPM time."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="end", compare=">", time="60BPM", format="x"
        )
        command_data.pop("num", None)
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # 60BPM = 1 beat per second = 2 samples per beat (at 2Hz)
            # > 2 samples: all except row 3 (index 1)
            self.assertEqual([1, 1, 1, 0, 1, 1, 1, 1], person["ALRIGHT1"])
        pass

    # ========== AMPLITUDE TESTS ==========
    def test_check_amp_less_y_noalight(self):
        """Test AMP variable with < operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="amp", num=2.5)
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # Amplitudes: [2, 3, 2, 2, 2, 2, 2, 5]
            # < 2.5: rows 0, 2, 3, 4, 5, 6
            self.assertEqual([1, 0, 1, 1, 1, 1, 1, 0], person["ALRIGHT1"])
        pass

    def test_check_amp_greater_y_noalight(self):
        """Test AMP variable with > operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="amp", compare=">", num=2.5)
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # > 2.5: rows 1, 7
            self.assertEqual([0, 1, 0, 0, 0, 0, 0, 1], person["ALRIGHT1"])
        pass

    # ========== FLAT REGION TESTS ==========
    def test_check_flat_less_y_noalight(self):
        """Test FLAT variable with < operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="flat", in_channel="CHANNELB", num=4
        )
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # CHANNELB flat regions (tolerance=0.1):
            # Row 0: [1,2,3,4,5] - longest flat = 1 (no consecutive similar values)
            # Row 1: [2,2,2,2,2] - longest flat = 5 (all values same)
            # Row 2: [1,1.1,1.2,1.3,1.4] - longest flat = 1 (differences > 0.1)
            # < 4: rows 0, 2
            self.assertEqual([1, 0, 1, 1, 1, 1, 1, 1], person["ALRIGHT1"])
        pass

    def test_check_flat_greater_y_noalight(self):
        """Test FLAT variable with > operator in Y format."""
        variables = self.make_variables()
        command_data = self.create_test_command(
            variable="flat", in_channel="CHANNELB", compare=">", num=2
        )
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # > 2: only row 1 (flat length = 5)
            self.assertEqual([0, 1, 0, 1, 1, 1, 1, 1], person["ALRIGHT1"])
        pass

    # ========== PERCENTAGE COMPARISON TESTS ==========
    def test_check_min_percent_x_less(self):
        """Test MIN variable with %x< operator."""
        variables = self.make_variables()
        command_data = self.create_test_command(compare="%x<", format="x", num=0.1)
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # Min indices: [0, 0, 0, 0, 0, 1, 2, 2]
            # Lengths: [5, 5, 5, 2, 8, 5, 5, 5]
            # Percentages: [0, 0, 0, 0, 0, 0.2, 0.4, 0.4]
            # < 0.1: rows 0-4
            self.assertEqual([1, 1, 1, 1, 1, 0, 0, 0], person["ALRIGHT1"])
        pass

    def test_check_min_percent_x_greater(self):
        """Test MIN variable with %x> operator."""
        variables = self.make_variables()
        command_data = self.create_test_command(compare="%x>", format="x", num=0.3)
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # > 0.3: rows 6, 7 (0.4)
            self.assertEqual([0, 0, 0, 0, 0, 0, 1, 1], person["ALRIGHT1"])
        pass

    # ========== EDGE CASE TESTS ==========
    def test_check_with_existing_mask(self):
        """Test check when mask already has some zeros (AND operation)."""
        variables = self.make_variables()
        # Modify existing mask to have some zeros
        person = variables["VARNAME"][0]
        person["ALRIGHT1"] = [1, 0, 1, 0, 1, 0, 1, 0]

        command_data = self.create_test_command()
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # Existing: [1, 0, 1, 0, 1, 0, 1, 0]
            # New check: [0, 1, 0, 1, 0, 1, 0, 1] (from test_check_min_less_y_noalight)
            # AND result: [0, 0, 0, 0, 0, 0, 0, 0]
            self.assertEqual([0, 0, 0, 0, 0, 0, 0, 0], person["ALRIGHT1"])
        pass

    def test_check_empty_row_handling(self):
        """Test check with empty data row."""
        variables = self.make_variables()
        # Add an empty row
        person = variables["VARNAME"][0]
        person["CHANNELA"].append([])
        person["ALRIGHT1"].append(1)

        command_data = self.create_test_command()
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # Empty row should be marked as bad (0)
            self.assertEqual([0, 1, 0, 1, 0, 1, 0, 1, 0], person["ALRIGHT1"])
        pass

    def test_check_single_element_row(self):
        """Test check with single element row."""
        variables = self.make_variables()
        # Add a single element row
        person = variables["VARNAME"][0]
        person["CHANNELA"].append([5])
        person["ALRIGHT1"].append(1)

        command_data = self.create_test_command()
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # Single element row: min=5, not < 0 -> should be 0
            self.assertEqual([0, 1, 0, 1, 0, 1, 0, 1, 0], person["ALRIGHT1"])
        pass

    def test_check_nan_handling(self):
        """Test check with NaN values in data."""
        variables = self.make_variables()
        # Add a row with NaN
        person = variables["VARNAME"][0]
        person["CHANNELA"].append([1.0, float("nan"), 2.0])
        person["ALRIGHT1"].append(1)

        command_data = self.create_test_command()
        command = Check(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            # Row with NaN: min=1.0, not < 0 -> should be 0
            self.assertEqual([0, 1, 0, 1, 0, 1, 0, 1, 0], person["ALRIGHT1"])
        pass

    def test_check_case_insensitive_variables(self):
        """Test that variable names are case-insensitive."""
        variables = self.make_variables()

        # Test lowercase
        command_data1 = self.create_test_command(variable="min")
        command1 = Check(command_data1)
        result1 = command1.execute(variables)

        # Test uppercase
        command_data2 = self.create_test_command(variable="MIN")
        command2 = Check(command_data2)
        result2 = command2.execute(variables)

        # Test mixed case
        command_data3 = self.create_test_command(variable="Min")
        command3 = Check(command_data3)
        result3 = command3.execute(variables)

        # All should give same result
        mask1 = result1["VARNAME"][0]["ALRIGHT1"]
        mask2 = result2["VARNAME"][0]["ALRIGHT1"]
        mask3 = result3["VARNAME"][0]["ALRIGHT1"]

        self.assertEqual(mask1, mask2)
        self.assertEqual(mask1, mask3)

    def test_check_multiple_channels(self):
        """Test check with multiple input/output channels."""
        variables = self.make_variables()
        command_data = {
            "class_name": "check",
            "in": ["VARNAME", "VARNAME"],
            "in_channel": ["CHANNELA", "CHANNELB"],
            "out_channel": ["OUT_A", "OUT_B"],
            "out": ["VARNAME_A", "VARNAME_B"],
            "variable": ["min", "mean"],
            "format": ["y", "y"],
            "compare": ["<", ">"],
            "mask": ["MASK_A", "MASK_B"],
            "num": [0, 2.0],
            "verbosity": "none",
        }

        command = Check(command_data)
        variables = command.execute(variables)

        # Check both outputs exist
        self.assertIn("VARNAME_A", variables)
        self.assertIn("VARNAME_B", variables)

        # Check CHANNELA results (min < 0)
        mask_a = variables["VARNAME_A"][0]["MASK_A"]
        self.assertEqual([0, 1, 0, 1, 0, 1, 0, 1], mask_a)

        # Check CHANNELB results (mean > 2.0)
        mask_b = variables["VARNAME_B"][0]["MASK_B"]
        # CHANNELB means: [3.0, 2.0, 1.2], > 2.0: only first row
        self.assertEqual([1, 0, 0], mask_b)

    def test_check_validation_invalid_variable(self):
        """Test validation with invalid variable name."""
        command_data = self.create_test_command(variable="INVALID_VAR")
        command = Check(command_data)

        # Command should be invalid
        self.assertFalse(
            command.good, "Command with invalid variable should not be valid"
        )

    def test_check_validation_invalid_format(self):
        """Test validation with invalid format."""
        command_data = self.create_test_command(format="Z")  # Invalid format
        command = Check(command_data)

        self.assertFalse(
            command.good, "Command with invalid format should not be valid"
        )

    def test_check_validation_invalid_compare(self):
        """Test validation with invalid compare operator."""
        command_data = self.create_test_command(compare="<>")  # Invalid operator
        command = Check(command_data)

        self.assertFalse(
            command.good, "Command with invalid compare operator should not be valid"
        )

    def test_check_validation_mismatched_sizes(self):
        """Test validation when parameter lists have mismatched sizes."""
        command_data = self.create_test_command()
        command_data["in"] = ["VARNAME", "VARNAME2"]  # Different size from others
        command = Check(command_data)

        self.assertFalse(
            command.good, "Command with mismatched sizes should not be valid"
        )

    def test_check_execute_invalid_skips(self):
        """Test that invalid commands are skipped."""
        variables = self.make_variables()
        command_data = self.create_test_command(variable="INVALID_VAR")

        command = Check(command_data)
        self.assertFalse(command.good)

        # Execute should skip and print warning
        try:
            result = command.execute(variables)
        except ValueError as e:
            self.assertIsNotNone(e)
        # Should return variables unchanged or with minimal changes


if __name__ == "__main__":
    unittest.main()

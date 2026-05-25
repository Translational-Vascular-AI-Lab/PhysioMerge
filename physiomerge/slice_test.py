import unittest
from slice import Slice  # type: ignore


class SliceTest(unittest.TestCase):
    def make_variables(self):
        variables = {}
        people = []
        person = {}
        person["FREQUENCY"] = 2
        person["FILENAME"] = "testing"
        person["CHANNELA"] = [
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        ]
        person["CHANNELB"] = [[1], [2], [5], [10]]
        people.append(person)
        variables["VARNAME"] = people
        return variables

    def make_command(self, **kwargs):
        command_data = {}
        command_data["class_name"] = "Slice"
        command_data["in"] = "VARNAME"
        command_data["in_channel"] = "CHANNELA"
        command_data["end"] = 0.9
        command_data["start"] = 0.1
        command_data["out_channel"] = "OUT"
        command_data["out"] = "VARNAME"
        command_data["verbosity"] = "none"
        command_data.update(kwargs)
        return command_data

    def test_slice(self):
        """Test basic slicing with start=0.6, end=0.9"""
        variables = self.make_variables()
        command_data = self.make_command()
        command_data["end"] = 0.9
        command_data["start"] = 0.6
        command = Slice(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            self.assertEqual(
                [[7, 8, 9], [70, 80, 90], [700, 800, 900], [0.7, 0.8, 0.9]],
                person["OUT"],
            )
        pass

    def test_slice_bad_start_lower(self):
        """Test with start below 0 (should clamp to 0)"""
        variables = self.make_variables()
        command_data = self.make_command()
        command_data["end"] = 0.1
        command_data["start"] = -0.1
        command = Slice(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            self.assertEqual(
                [[1], [10], [100], [0.1]],
                person["OUT"],
            )
        pass

    def test_slice_bad_toohighstart(self):
        """Test when start > end (should error)"""
        variables = self.make_variables()
        command_data = self.make_command()
        command_data["end"] = 0.1
        command_data["start"] = 0.2
        command = Slice(command_data)
        try:
            variables = command.execute(variables)
            self.assertIsNone(variables)
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_slice_bad_toohighend(self):
        """Test with end above 1 (should clamp to 1)"""
        variables = self.make_variables()
        command_data = self.make_command()
        command_data["end"] = 1.2
        command_data["start"] = 0.9
        command = Slice(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            self.assertEqual(
                [[10], [100], [1000], [1.0]],
                person["OUT"],
            )
        pass

    def test_slice_first_half(self):
        """Test slicing first half (0.0 to 0.5)"""
        variables = self.make_variables()
        command_data = self.make_command()
        command_data["start"] = 0.0
        command_data["end"] = 0.5
        command = Slice(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            self.assertEqual(
                [
                    [1, 2, 3, 4, 5],
                    [10, 20, 30, 40, 50],
                    [100, 200, 300, 400, 500],
                    [0.1, 0.2, 0.3, 0.4, 0.5],
                ],
                person["OUT"],
            )

    def test_slice_middle(self):
        """Test slicing middle section (0.3 to 0.7)"""
        variables = self.make_variables()
        command_data = self.make_command()
        command_data["start"] = 0.3
        command_data["end"] = 0.7
        command = Slice(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            self.assertEqual(
                [
                    [4, 5, 6, 7],
                    [40, 50, 60, 70],
                    [400, 500, 600, 700],
                    [0.4, 0.5, 0.6, 0.7],
                ],
                person["OUT"],
            )

    def test_slice_single_element(self):
        """Test slicing a single element (0.4 to 0.5)"""
        variables = self.make_variables()
        command_data = self.make_command()
        command_data["start"] = 0.4
        command_data["end"] = 0.5
        command = Slice(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            self.assertEqual(
                [[5], [50], [500], [0.5]],
                person["OUT"],
            )

    def test_slice_entire_range(self):
        """Test slicing entire range (0.0 to 1.0)"""
        variables = self.make_variables()
        command_data = self.make_command()
        command_data["start"] = 0.0
        command_data["end"] = 1.0
        command = Slice(command_data)
        variables = command.execute(variables)

        if variables["VARNAME"] == []:
            raise KeyError
        for person in variables["VARNAME"]:
            self.assertEqual(
                [
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                    [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                    [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
                    [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                ],
                person["OUT"],
            )


if __name__ == "__main__":
    unittest.main()

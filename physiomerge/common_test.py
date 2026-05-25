import unittest
import numpy as np

from common import find_indices, copy_dict, time_from_string, Command


class TestCommonFunctions(unittest.TestCase):

    # ----------------------------
    # Tests for find_indices
    # ----------------------------
    def test_find_indices_empty_list(self):
        self.assertEqual(find_indices(5, []), [])

    def test_find_indices_not_found(self):
        self.assertEqual(find_indices(5, [1, 2, 3, 4]), [])

    def test_find_indices_single_occurrence(self):
        self.assertEqual(find_indices(3, [1, 2, 3, 4]), [2])

    def test_find_indices_multiple_occurrences(self):
        self.assertEqual(find_indices(2, [1, 2, 3, 2, 4, 2]), [1, 3, 5])

    def test_find_indices_all_same(self):
        self.assertEqual(find_indices(7, [7, 7, 7, 7]), [0, 1, 2, 3])

    # ----------------------------
    # Tests for copy_dict
    # ----------------------------
    def test_copy_dict_simple(self):
        original = {"a": 1, "b": 2}
        copy = copy_dict(original)
        self.assertEqual(copy, original)
        copy["a"] = 100
        self.assertEqual(original["a"], 1)  # Original unchanged

    def test_copy_dict_with_numpy_array(self):
        arr = np.array([1, 2, 3])
        original = {"arr": arr}
        copy = copy_dict(original)
        self.assertTrue(np.array_equal(copy["arr"], arr))
        copy["arr"][0] = 100
        self.assertEqual(arr[0], 1)  # Original array unchanged

    def test_copy_dict_nested_dict(self):
        original = {"outer": {"inner": 5}}
        copy = copy_dict(original)
        self.assertEqual(copy, original)
        copy["outer"]["inner"] = 100
        self.assertEqual(
            original["outer"]["inner"], 5
        )  # Original nested dict unchanged

    def test_copy_dict_mixed_types(self):
        arr = np.array([1, 2])
        original = {"num": 42, "arr": arr, "nested": {"key": "val"}}
        copy = copy_dict(original)
        self.assertEqual(copy["num"], 42)
        self.assertTrue(np.array_equal(copy["arr"], arr))
        self.assertEqual(copy["nested"]["key"], "val")
        copy["arr"][0] = 99
        copy["nested"]["key"] = "new"
        self.assertEqual(arr[0], 1)
        self.assertEqual(original["nested"]["key"], "val")

    # ----------------------------
    # Tests for time_from_string
    # ----------------------------
    def test_time_from_string_seconds(self):
        self.assertEqual(time_from_string("10s", 1000), 10000)

    def test_time_from_string_milliseconds(self):
        self.assertEqual(time_from_string("500ms", 1000), 500)

    def test_time_from_string_microseconds(self):
        self.assertEqual(time_from_string("2000us", 1000), 2)

    def test_time_from_string_minutes_and_hours(self):
        self.assertEqual(time_from_string("1m", 2), 120)
        self.assertEqual(time_from_string("1hr", 1), 3600)
        self.assertEqual(time_from_string("1h30m", 1), 5400)

    def test_time_from_string_combined_units(self):
        # 1s + 500ms + 200ms = 1.7s, sampling 10 Hz => 17 samples
        self.assertEqual(time_from_string("1s500ms200ms", 10), 17)

    def test_time_from_string_Hz(self):
        self.assertEqual(time_from_string("10Hz", 1000), 100)
        self.assertEqual(time_from_string("2kHz", 10000), 5)
        self.assertEqual(time_from_string("0.5MHz", 1_000_000), 2)

    def test_time_from_string_BPM(self):
        self.assertEqual(time_from_string("60BPM", 1), 1)
        self.assertEqual(time_from_string("120BPM", 2), 1)

    def test_time_from_string_unknown_unit(self):
        with self.assertRaises(ValueError):
            time_from_string("5xyz", 1000)

    def test_time_from_string_fractional_values(self):
        self.assertEqual(time_from_string("0.5s", 10), 5)
        self.assertEqual(time_from_string("0.25min", 60), 900)


class TestCommand(unittest.TestCase):

    def setUp(self):
        self.cmd_dict = {
            "class_name": "test",
            "in": "input",
            "in_channel": "chan",
            "out": "output",
            "out_channel": "out_chan",
            "verbosity": "none",
        }
        self.cmd = Command(self.cmd_dict)

    # ------------------------
    # __init__ and __repr__
    # ------------------------
    def test_init_attributes(self):
        self.assertEqual(self.cmd.type, "TEST")
        self.assertEqual(self.cmd.name, "input")
        self.assertEqual(self.cmd.channel, "chan")
        self.assertEqual(self.cmd.resultant, "output")
        self.assertEqual(self.cmd.out_channel, "out_chan")
        self.assertEqual(self.cmd.order, "none")
        self.assertFalse(self.cmd.good)

    def test_repr_contains_all_attributes(self):
        r = repr(self.cmd)
        for attr in [
            "type",
            "name",
            "channel",
            "resultant",
            "out_channel",
            "order",
            "good",
        ]:
            self.assertIn(attr, r)

    # ------------------------
    # validate
    # ------------------------
    def test_validate_valid(self):
        self.assertTrue(self.cmd.validate())

    def test_validate_invalid_type(self):
        self.cmd.type = None
        try:
            self.assertFalse(self.cmd.validate())
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_validate_invalid_order_value(self):
        self.cmd.order = "invalid"
        self.cmd.validate()
        self.assertEqual(self.cmd.order, "command")
        self.cmd.order = "none"

    # ------------------------
    # equal_size
    # ------------------------
    def test_equal_size_lists(self):
        self.cmd.var1 = [1, 2]
        self.cmd.var2 = [3, 4]
        self.cmd.equal_size(["var1", "var2"])
        self.assertEqual(self.cmd.var1, [1, 2])

    def test_equal_size_scalar_expand(self):
        self.cmd.var1 = 5
        self.cmd.var2 = [1, 2, 3]
        self.cmd.equal_size(["var1", "var2"])
        self.assertEqual(self.cmd.var1, [5, 5, 5])

    def test_equal_size_value_error(self):
        self.cmd.var1 = [1]
        self.cmd.var2 = [1, 2]
        with self.assertRaises(ValueError):
            self.cmd.equal_size(["var1", "var2"])

    # ------------------------
    # check_type_inner / check_value_type / list_inner
    # ------------------------
    def test_check_type_inner_true(self):
        self.assertTrue(self.cmd.check_type_inner(["type", "name"], [str]))

    def test_check_type_inner_false(self):
        self.cmd.type = 1
        try:
            self.assertFalse(self.cmd.check_type_inner(["type"], [str]))
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_check_value_type_list_nested(self):
        self.assertTrue(self.cmd.check_value_type([["a", "b"]], [str]))
        self.assertFalse(self.cmd.check_value_type([["a", 1]], [str]))

    def test_list_inner(self):
        self.assertTrue(self.cmd.list_inner([["x", "y"], ["a"]], [str]))
        self.assertFalse(self.cmd.list_inner([["x", 1]], [str]))

    # ------------------------
    # print (verbosity)
    # ------------------------
    def test_print_crash(self):
        try:
            self.cmd.print("crash", "boom")
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_print_none(self):
        self.cmd.order = "none"
        # Should not raise
        self.cmd.print("debug", "test")

    # ------------------------
    # check_all / check_any
    # ------------------------
    def test_check_all(self):
        self.assertTrue(self.cmd.check_all([1, 2, 3], lambda x: x > 0))
        self.assertFalse(self.cmd.check_all([1, 0, 3], lambda x: x > 0))

    def test_check_any(self):
        self.assertTrue(self.cmd.check_any([0, 0, 1], lambda x: x > 0))
        self.assertFalse(self.cmd.check_any([0, 0, 0], lambda x: x > 0))

    # ------------------------
    # debug_data
    # ------------------------
    def test_debug_data(self):
        s = self.cmd.debug_data(a=1, b="x")
        self.assertIn("'a':'1'", s)
        self.assertIn("'b':'x'", s)

    # ------------------------
    # string_upper
    # ------------------------
    def test_string_upper_single(self):
        self.cmd.name = "hello"
        self.cmd.string_upper(["name"])
        self.assertEqual(self.cmd.name, "HELLO")

    def test_string_upper_list(self):
        self.cmd.list_attr = ["a", "b"]
        self.cmd.string_upper(["list_attr"])
        self.assertEqual(self.cmd.list_attr, ["A", "B"])

    # ------------------------
    # ensure_alright
    # ------------------------
    def test_ensure_alright_existing(self):
        person = {"chan": [1, 2], "ok": [0, 1]}
        res = self.cmd.ensure_alright(person, "chan", "ok")
        self.assertEqual(res, [0, 1])

    def test_ensure_alright_missing(self):
        person = {"chan": [1, 2]}
        res = self.cmd.ensure_alright(person, "chan", "ok")
        self.assertEqual(res, [1, 1])

    def test_ensure_alright_none(self):
        person = {"chan": [1, 2]}
        res = self.cmd.ensure_alright(person, "chan", "")
        self.assertEqual(res, [1, 1])

    # ------------------------
    # ensure_channel
    # ------------------------
    def test_ensure_channel_exists(self):
        person = {"chan": [1, 2], "other": [[1], [1]]}
        res = self.cmd.ensure_channel(person, "chan", "other")
        self.assertEqual(res, [[1], [1]])

    def test_ensure_channel_missing(self):
        person = {"chan": [1, 2]}
        res = self.cmd.ensure_channel(person, "chan", "other")
        self.assertEqual(res, [[1], [1]])

    def test_ensure_channel_none(self):
        person = {"chan": [1, 2]}
        res = self.cmd.ensure_channel(person, "chan", "")
        self.assertEqual(res, [[1], [1]])

    # ------------------------
    # is_in_array
    # ------------------------
    def test_is_in_array_str_valid(self):
        self.assertTrue(self.cmd.is_in_array("a", ["a", "b"]))

    def test_is_in_array_str_invalid(self):
        try:
            self.assertFalse(self.cmd.is_in_array("c", ["a", "b"]))
        except ValueError as e:
            self.assertIsNotNone(e)

    def test_is_in_array_list_valid(self):
        self.assertTrue(self.cmd.is_in_array(["a", "b"], ["a", "b", "c"]))

    def test_is_in_array_list_invalid(self):
        try:
            self.assertFalse(self.cmd.is_in_array(["a", "d"], ["a", "b", "c"]))

        except ValueError as e:
            self.assertIsNotNone(e)


if __name__ == "__main__":
    unittest.main()

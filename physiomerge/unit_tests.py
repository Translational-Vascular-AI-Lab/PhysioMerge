import unittest

from common_test import TestCommonFunctions, TestCommand

# Analysis of Data
from check_test import CheckTest
from take_test import TakeTest
from priority_test import PriorityTest
from merge_test import MergeTest

# Modification of Data
from filter_test import FilterTest
from cut_test import CutTest
from partition_test import PartitionTest
from adjust_test import AdjustTest
from normalize_test import NormalizeTest
from aggregate_test import AggregateTest
from measurement_test import MeasurementTest
from arithmetic_test import ArithmeticTest
from marker_test import MarkerTest
from morphology_test import MorphologyTest


if __name__ == "__main__":
    unittest.main()

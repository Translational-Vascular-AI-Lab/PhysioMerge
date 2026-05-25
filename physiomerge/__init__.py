"""
PhysioMerge Package
===================

PhysioMerge is a Python package for processing and merging physiological
signal data. It provides a unified command interface to manipulate,
adjust, and analyze datasets.

Modules
-------
adjust : Adjust channel data
aggregate : Aggregate multiple datasets
arithmetic : Perform arithmetic operations on signals
check : Validate dataset integrity
...
"""

# Import main commands for easy access
from adjust import Adjust
from aggregate import Aggregate
from arithmetic import Arithmetic
from check import Check
from cut import Cut
from expand import Expand
from filter import Filter
from find_wave import FindWave
from read import Read
from measurement import Measurement
from merge import Merge
from marker import Marker
from morphology import Morphology
from normalize import Normalize
from partition import Partition
from plot import Plot
from priority import Priority
from take import Take
from save import Save
from slice import Slice
from interpolate import Interpolate
from intersecting_tangent import IntersectingTangent

# Unified command registry
COMMANDS = {
    "adjust": Adjust,
    "aggregate": Aggregate,
    "arithmetic": Arithmetic,
    "check": Check,
    "cut": Cut,
    "expand": Expand,
    "filter": Filter,
    "peaks": FindWave,
    "interpolate": Interpolate,
    "marker": Marker,
    "measurement": Measurement,
    "merge": Merge,
    "morphology": Morphology,
    "normalize": Normalize,
    "partition": Partition,
    "plot": Plot,
    "priority": Priority,
    "read": Read,
    "save": Save,
    "slice": Slice,
    "take": Take,
    "inttan": IntersectingTangent,
}

__all__ = [
    "Adjust",
    "Aggregate",
    "Arithmetic",
    "Check",
    "Cut",
    "Expand",
    "Filter",
    "FindWave",
    "Read",
    "Measurement",
    "Merge",
    "Marker",
    "Morphology",
    "Normalize",
    "Partition",
    "Plot",
    "Priority",
    "Take",
    "Save",
    "Slice",
    "Interpolate",
    "IntersectingTangent",
    "COMMANDS",
]

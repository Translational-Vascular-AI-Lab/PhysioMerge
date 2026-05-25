import tomllib
import argparse
from pathlib import Path

"""
Command registry for LabchartParser.
"""

# Import all available commands
from physiomerge.adjust import Adjust
from physiomerge.aggregate import Aggregate
from physiomerge.arithmetic import Arithmetic
from physiomerge.check import Check
from physiomerge.cut import Cut
from physiomerge.expand import Expand
from physiomerge.filter import Filter
from physiomerge.find_wave import FindWave
from physiomerge.read import Read
from physiomerge.measurement import Measurement
from physiomerge.merge import Merge
from physiomerge.marker import Marker
from physiomerge.morphology import Morphology
from physiomerge.normalize import Normalize
from physiomerge.partition import Partition
from physiomerge.plot import Plot
from physiomerge.priority import Priority
from physiomerge.take import Take
from physiomerge.save import Save
from physiomerge.slice import Slice
from physiomerge.interpolate import Interpolate
from physiomerge.intersecting_tangent import IntersectingTangent

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

__all__ = ["COMMANDS"]

# PhysioMerge

PhysioMerge is a modular, configuration-driven tool for automated extraction, validation, and analysis of physiological data from LabChart and other recording systems. It is designed to replace manual data extraction with a reproducible, fast pipeline that supports batch processing, cycle-level validation, and advanced waveform morphology analysis.

PhysioMerge is designed for cardiovascular, cerebrovascular, and respiratory research workflows. Physiomerge supports processing of data where signal quality can vary across different devices and time. Additiionally, it is deisnged for instances where data validity is critical.

## Citation

If you use PhysioMerge in your research, please cite:

<-- Edit this once the paper is published -->
Abbasi-Hashemi, T., & Al-Khazraji, B. K.
_PhysioMerge: A tool for physiological data extraction and analysis_. 2025.
<-- Edit this once the paper is published -->

## Required Libraries

- Scipy
- Pandas
- Numpy
- TermColor
- Filterpy
- matplotlib
- logging
- os
- datetime
- ADI **Currently only supports Windows systems. You can use Physiomerge but reading raw Labchart files will not be supported outside of Windows. (This is a ADI problem, and can not be fixed)**

## Configuration Files

PhysioMerge workflows are defined entirely in TOML configuration files.The purpose of these configuration files is to ensure the exact methodology can be recorded and repeated by others.

The configuration of each command is unique to the command requirements. Read the documentation on the induvidual commands or see the examples for more information on how to use the commands.

The configuration files are read in the order they are provided to Physiomerge.

## How to use Physiomerge

> Python3 /physiomerge_path/cli.py configuration_file_path

Feedback is based on program verbosity. Use `-v` to edit the verbosity. The verbosity options are listed below

- "index"
- "debug"
- "command"
- "warning"
- "error"
- "none"

## To Validate Your System

A demo script can be run with

> python3 .\physiomerge\cli.py .\scripts\demo_scripts\demo.toml

To run a unit test on your data to ensure all the functions work as expected please run

> python3 .\physiomerge\unit_tests.py

## Command Summary

You can find more detailed information about the commands in the documentation file. Below is a list of supported commands and what they do.

### Data I/O

- **read** – Batch-load physiological data files
- **save** – Export selected variables to CSV, TSV, or TXT with flexible formatting

### Validation and Selection

- **check** – Apply physiological validity rules and generate binary masks
- **merge** – Combine validation masks using logical operators (AND / OR)
- **take** – Extract time-based or cycle-based subsets of valid data
- **priority** – Define fallback extraction rules when ideal conditions are not met

### Signal Modification

- **filter** – Apply frequency, moving-window, or adaptive filters
- **cut** – Segment data by time or annotated comments
- **partition** – Divide signals into physiological cycles (e.g., heartbeats, breaths)
- **slice** – Extract specific portions of each cycle
- **interpolate** – Resample signals or standardize waveform lengths
- **normalize** – Scale data to user-defined numeric ranges
- **adjustment** – Align and integrate external datasets using timeline markers

### Analysis and Feature Extraction

- **peaks** – Detect physiological events (e.g., systolic peaks, breaths)
- **measurement** – Extract scalar metrics (min, max, mean, period, amplitude)
- **arithmetic** – Perform mathematical operations on measurements
- **aggregation** – Compute summary statistics across cycles or segments
- **morphology** – Extract waveform shape features (e.g., curvature, slopes, AUC)
- **marker** – Compute timing differences between indexes

### Visualization

- **plot** – Generate multi-channel plots with markers and export-ready figures

# Data IO Commands

## Read Command

Batch-load physiological data files

The "READ" command is used for reading structured data from various file formats (LabChart, ADI, Terason, Respirac). It supports multi-channel data, variable sampling frequencies, and annotation extraction.

### Imports:

- **adi** for reading ADI LabChart files

### Example:

An example of a Read command configuration:

```toml
[[command]]
class_name = "read"
folder = "datasets/shch/labchart/"
file = ["SHCH_106_V1"]
ext = ".adicht"
format = "ADI"
out = "variable_name"
```

### Explanation of keys:

- **folder**: The folder where the files are located.
- **file**: The filename or list of filenames to read.
- **ext**: The file extension (e.g., ".adicht").
- **format**: The file format type. Supported values: `"LABCHART"`, `"ADI"`, `"TERASON"`, `"RESPIRAC"`.

## Save Command

Export selected variables to CSV, TSV, or TXT with flexible formatting.

The `"SAVE"` command is used to export processed or raw variables into text-based files. It supports custom delimiters, headers, and flexible variable ordering. Files can be overwritten or appended to, depending on user preference.

### Example:

An example of a Save command configuration:

```toml
[[command]]
class_name = "save"
in = ["data"]
append = [false]
header = ["person, time, DIAS_BP, MEAN_BP, SYS_BP, HR"]
format = "{filename}, {name}, {dias_bp}, {mean_bp}, {sys_bp}, {mean_hr},"
folder = "features/"
delim = ", "
decimal = 2
save_name = "output.csv"
```

### Explanation of keys:

- **folder**: The folder where the output file should be saved.
- **save_name**: The name of the output file.
- **delim**: The delimiter used between variables. Default is ",".
- **format**: The order and formatting of variables to be written. Supports placeholders for channel names ({time}, {mean_bp}).
- **header**: Optional header line for the file. Can be left blank if not needed.
- **append**: Determines whether to overwrite (false) or append (true) to an existing file.
- **decimal**: The number of decimals to round to, by default it is 2

# Analysis and Checking Data

## Check Command

Apply conditional checks to data channels with statistical measures and comparisons

The "CHECK" command validates data quality by applying statistical measures to data rows and comparing them against thresholds. It updates mask channels to indicate which data rows pass the specified conditions, supporting various statistical variables, comparison operators, and both absolute and percentage-based checks.

### Example

```toml
[[command]]
class_name = "check"
in = ["ecg_data"]
in_channel = ["heart_rate"]
out = ["filtered_ecg"]
mask = "quality_mask"
variable = "max"
format = "y"
compare = "<"
num = 120
time = "30s"
```

### Explanation of Keys

- **mask**: Name of the mask channel to update based on check results.
- **variable**: Statistical measure to calculate. One of:
  - _MAX_: Maximum value in the row
  - _MIN_: Minimum value in the row
  - _MEAN_: Mean (average) value
  - _MEDIAN_: Median value
  - _START_: Second element value (index 1)
  - _END_: Last element value
  - _AMP_: Amplitude (max - min)
  - _FLAT_: Length of longest flat region (values within 0.1 tolerance)
- **format**: Whether to compare the value ("Y") or its position/index ("X").
  - Basic: <, >, <=, >=, ==, !=
  - Percentage of X: %x<, %x>, %x<=, %x>=, %x==, %x!=
    <-- - Percentage of Y: %y<, %y>, %y<=, %y>=, %y==, %y!= no longer supported -->
- **num**: Threshold value(s) to compare against (float, int, or list).
- **time**: Optional time string that overrides num when specified. Converts time to number of samples based on FREQUENCY (e.g., "30s", "60BPM").

## Take Command

Extract subsets of data waves based on count, duration, or maximum available valid data

The "TAKE" command selects specific portions of data channels based on wave count, time duration, or maximum available valid data. It searches through data waves in either forward or backward direction, with options to require consecutive valid waves or take all available data.

### Example

```toml
[[command]]
class_name = "take"
in = ["ecg_data"]
in_channel = ["heartbeat_waves"]
out = ["selected_ecg"]
out_channel = ["analysis_waves"]
waves = 10
time = "30s"
mask = "quality_mask"
consecutive = true
direction = "+"
maximum = false
```

### Explanation of Keys

- **waves**: Number of waves to select (integer, 0 if using time or maximum). If this isn't 0 or empty, it will take priority over time
- **time**: Time duration to select (e.g., "30s", "5m", "60BPM"). Takes priority unless waves > 0.
- **mask**: Name of the mask channel used to identify valid waves (1=valid, 0=invalid).
- **consecutive**: Whether to require consecutive valid waves (true/false).
- **direction**: Search direction for waves. "+" = forward from start, "-" = backward from end.
- **maximum**: Whether to select all available valid waves (true/false). Overrides waves and time.

## Priority Command

Select data from the first available non-empty channel in a priority order

The "PRIORITY" command provides fallback selection logic for data channels. It checks channels in a specified order and selects data from the first channel that exists and contains non-empty data. This is useful when multiple processing paths may produce results, and you want to use the first successful result.

### Example

```toml
[[command]]
class_name = "priority"
in = ["processed_data"]
channels = ["primary_result", "secondary_result", "fallback_result"]
out = ["final_data"]
out_channel = "selected_output"
```

### Explanation of Keys

- **channels**: Ordered list of channel names to check for data. First non-empty channel wins.

## Merge Command

Combine or compare data from two channels using logical operations or length comparisons

The "MERGE" command performs operations on data from two channels, either combining them element-wise using logical operations (AND, OR, XOR, etc.) or selecting between them based on length comparisons (greater, lesser). This is useful for combining mask channels, selecting between alternative data sources, or creating composite data sets.

### Example

```toml
[[command]]
class_name = "merge"
in = ["processed_data"]
in_channel = ["quality_mask1"]
in_channel_2 = "quality_mask2"
out = ["merged_data"]
out_channel = "combined_mask"
format = "AND"
```

### Explanation of Keys

- **in_channel_2**: Name of the second channel to merge with the first channel.
- **format**: Operation to apply when merging. One of:
  - _greater_: Select the channel with more elements
  - _lesser_: Select the channel with fewer elements
  - _AND_: Logical AND (element-wise)
  - _OR_: Logical OR (element-wise)
  - _NAND_: Logical NAND (element-wise)
  - _NOR_: Logical NOR (element-wise)
  - _XOR_: Logical XOR (element-wise)
  - _XNOR_: Logical XNOR (element-wise)

# Validation and Selection

## Filter Command

Apply signal processing filters to data channels for smoothing, noise reduction, and feature extraction

The "FILTER" command provides various signal processing techniques for filtering and transforming data channels. It supports multiple filter types including Butterworth for frequency-based filtering, Savitzky-Golay for polynomial smoothing, Kalman for optimal estimation, derivative for rate-of-change calculation, and sliding standardization for normalization.

### Example

```toml
[[command]]
class_name = "filter"
in = ["raw_signal"]
in_channel = ["ecg_signal"]
out = ["filtered_signal"]
out_channel = ["clean_ecg"]
function = "BUTTERWORTH"
power = 4
frequency = 40
ftype = "lowpass"
window = "0.5s"
time = ""
```

### Explanation of Keys

- **function**: Filter type to apply. One of:
  - _BUTTERWORTH_: Frequency-based IIR filter
  - _SAVGOL_: Savitzky-Golay polynomial smoothing filter
  - _KALMAN_: Kalman filter for optimal estimation
  - _DERIVATIVE_: Numerical derivative (rate of change)
  - _SLIDING_STANDARD_: Sliding window standardization
  - _AVERAGE_: A sliding window average
  - _FIR_: Finite Impulse Response Filter (Not yet tested)
- **power**: Filter order or polynomial order (integer).
- **frequency**: Cutoff frequency for Butterworth filter (Hz).
- **ftype**: Butterworth filter type. One of: "lowpass", "highpass", "bandpass", "bandstop".
- **window**: Window size for Savitzky-Golay or sliding standard filters (samples or time string).
- **time**: Time specification for window calculations.

## Cut Command

Extract or remove specific data segments based on comments, time intervals, or markers

The "CUT" command selects or removes segments from data files based on comment markers or time windows. It can extract periods between specific annotations, remove unwanted sections, or select fixed time intervals from recordings.

### Example

```toml
# Cut based on comments
[[command]]
class_name = "cut"
in = ["raw_recordings"]
out = ["selected_intervals"]
form = "COMMENT"
comment1 = "TASK_START"
comment2 = "TASK_END"
reset = true
boundary = ""

# Cut based on time
[[command]]
class_name = "cut"
in = ["long_recording"]
out = ["analysis_window"]
form = "TIME"
start = "30s"
period = "5m"
direction = "+"
boundary = ""
```

### Explanation of Keys

- **form**: Cutting method. One of:
  - _COMMENT_: Cut based on comment markers
  - _TIME_: Cut based on time intervals
- **comment1**: Starting comment(s) for comment-based cutting.
- **comment2**: Ending comment(s) for comment-based cutting.
- **reset**: Whether to stop at "RESET" comments (true/false).
- **period**: Time period/duration for time-based cutting.
- **start**: Start time offset for time-based cutting.
- **direction**: Time direction. "+" forward from start, "-" backward from end.
- **boundary**: Boundary handling. "" (keep segment) or _outside_ (remove segment).

## Partition Command

Segment time-series data into partitions based on marker indices

The "PARTITION" command divides continuous data streams into discrete segments (partitions) using marker columns as boundaries. Each partition represents a contiguous block of data between marker occurrences, allowing for event-based segmentation of recordings for analysis.

### Example

```toml
[[command]]
class_name = "partition"
in = ["continuous_data"]
out = ["partitioned_data"]
in_channel = ["EEG_CH1"]
out_channel = ["SEGMENTS"]
index = ["MARKER_COL"]
del_first = false
del_last = false
```

### Explanation of Keys

- **index**: Marker column(s) used to define partition boundaries. Partitions are created when the marker value appears in the markers list at each data row.
- **del_first**: Whether to remove the first partition from results (true/false).
- **del_last**: Whether to remove the last partition from results (true/false).

## Adjust Command

Align and transfer signals between synchronized data recordings

The "ADJUST" command copies or transfers data from a reference dataset to a primary dataset based on synchronization markers or comments. It aligns signals between different recording channels or systems by using event markers as temporal anchors, enabling cross-channel data integration and correction.

### Example

```toml
[[command]]
class_name = "adjust"
in = ["primary_data"]
in_2 = ["reference_data"]
out = ["adjusted_data"]
comments = ["STIMULUS_ON"]
in_channel_2 = ["EMG_SOURCE"]
out_channel = ["EMG"]
```

### Explanation of Keys

- **in_2**: Reference dataset name containing the source signal to be copied.
- **comments**: Comment marker(s) indicating where adjustments should be applied. The adjustment starts at the position of the last matching comment.
- **in_channel_2**: Channel name in the reference dataset containing the source data to copy.

## Slice Command

Extract percentage-based segments from partitioned data channels

The "SLICE" command takes specified percentage ranges from each data segment within a channel and stores the extracted portions in a new output channel. This is particularly useful for analyzing specific parts of partitioned data, such as the first 30% or middle 50% of each trial segment.

### Example

```toml
[[command]]
class_name = "slice"
in = ["partitioned_data"]
out = ["middle_segments"]
in_channel = ["EEG_TRIALS"]
out_channel = ["EEG_MIDDLE"]
start = 0.25
end = 0.75
```

### Explanation of Keys

- **start**: Starting percentage (0.0 to 1.0) of each segment to include in the slice.
- **end**: Ending percentage (0.0 to 1.0) of each segment to include in the slice.

## Normalize Command

Scale data segments to specified ranges using min-max normalization

The "NORMALIZE" command applies min-max scaling to each data segment independently, transforming values to fit within a user-defined range. This is essential for standardizing data amplitude across different recordings, channels, or experimental conditions, particularly useful for comparing signals with different baselines or amplitudes.

### Example

```toml
# This is most likely what you would use
[[command]]
class_name = "normalize"
in = ["raw_signals"]
out = ["standardized_data"]
in_channel = ["BP_RAW"]
out_channel = ["BP_NORMALIZED"]

# In case you don't want a 0-1 range, you can do whatever.
# This is a bipolar example.
[[command]]
class_name = "normalize"
in = ["emg_recordings"]
out = ["bipolar_signals"]
in_channel = ["BP_RAW"]
out_channel = ["BP_BiPolar"]
height = 2
shift = -1
```

### Explanation of Keys

- **height**: Desired amplitude/range of the output signal. Defines the difference between maximum and minimum values after normalization. Defaults to 1.

- **shift**: Baseline/offset value after normalization. Determines the minimum value of the output range. Defaults to 0.

## Aggregate Command

Perform statistical aggregations on data channels with optional masking and weighting.

The "AGGREGATE" command computes statistical summaries over data channels, supporting various aggregation methods including mean, weighted mean, variance, standard deviation, minimum, maximum, median, and mode. Data can be filtered using mask channels, and weights can be applied for weighted calculations. NaN values are automatically handled in all calculations.

### Example:

An example of a Save command configuration:

```toml
[[command]]
class_name = "aggregate"
in = ["ecg_data"]
in_channel = ["heart_rate"]
out = ["processed_ecg"]
out_channel = ["hr_mean"]
format = "mean"
mask = "quality_mask"
weights = "time_weights"
```

### Explanation of keys:

- **format**: Statistical aggregation method to apply.
- **mask**: Name of the mask channel used to filter data before aggregation. Only data points where mask value equals 1 are included. Leave empty ("") or do not include, to include all data.
- **weights**: Name of the channel containing weights for weighted mean calculations. LEave empty ("") or do not include, to have all values weighted equally.
  format: Statistical aggregation method to apply. One of:

Valid options for **FORMAT** are:

- mean: Arithmetic mean
- variance: Variance (population variance)
- std: Standard deviation
- min: Minimum value
- max: Maximum value
- median: Median value
- mode: Most frequent value

## Peaks Command

Detect peaks or valleys in time-series data using prominence, height, and distance constraints

The "PEAKS" command identifies local maxima (peaks) or minima (valleys) in continuous data channels. It doesn't have an output channel, instead it saves as markers of that particular channel. These markers are then used for other things.

### Example

```toml
[[command]]
class_name = "peaks"
in = ["raw_signals"]
out = ["peak_detected"]
in_channel = ["BP_CH1"]
difference = "200ms"
prominence = 0.5
height = 1.0
format = "MAX"
overwrite = false
```

### Explanation of Keys

- **difference**: Minimum time/sample distance between detected features. Can be specified as a time string (e.g., "100ms", "0.5s", "1s") or will be interpreted as number of samples if numeric.
- **prominence**: Minimum prominence of detected features. Prominence measures how much a feature stands out from the surrounding baseline.
- **height**: Minimum absolute height of detected features. For "MAX" format, detects peaks above this value; for "MIN" format, detects valleys below this value.
- **format**: Detection mode. "MAX" for detecting peaks (local maxima) or "MIN" for detecting valleys (local minima).
- **overwrite**: Determines if the previous existing markers should be deleted or not. True means that previous markers are deleted (overwritten), and false means they are not.

## Measurement Command

Calculate statistical metrics and signal characteristics on segmented data

The "MEASUREMENT" command computes various metrics on each segment within a data channel, providing both statistical summaries and signal properties. It operates independently on each segment, making it ideal for analyzing partitioned data from trials, cardiac cycles, or events.

### Example

```toml
[[command]]
class_name = "measurement"
in = ["BP_windows"]
out = ["BP_statistics"]
in_channel = ["BP", "BP", "BP"]
out_channel = ["Systolic_BP", "Diastolic_BP", "Pulse_Pressure"]
format = ["min", "max", "amplitude"]
```

### Explanation of Keys

- **format**: Type of measurement to calculate. Can be a single format or a list of formats for multiple operations.
  - _Statistical metrics_: "mean", "median", "mode", "min", "max"
  - _Signal characteristics_: "period", "amplitude", "frequency"

## Arithmatic Command

Perform element-wise arithmetic operations on data channels

The "ARITHMETIC" command applies mathematical operations to each element in data channels, supporting both channel-to-channel operations (where corresponding elements from two channels are combined) and channel-to-constant operations (where each element is combined with a fixed value).

### Example

```toml
# Add constant to channel
[[command]]
class_name = "arithmetic"
in = ["raw_signals"]
out = ["adjusted_signals"]
in_channel = ["EEG_CH1"]
out_channel = ["EEG_ADJUSTED"]
format = "+"
num = 5

# Multiply two channels together
[[command]]
class_name = "arithmetic"
in = ["processed_data"]
out = ["multiplied_data"]
in_channel = ["EMG_ENVELOPE"]
in_channel_2 = ["GAIN_FACTOR"]
out_channel = ["EMG_SCALED"]
format = "*"
```

### Explanation of Keys

- **format**: Arithmetic operation to perform:
  - _+_: Addition
  - _-_: Subtraction
  - _\*_: Multiplication
  - _/_: Division
  - _^_: Power (exponentiation)
  - _-1_: Reciprocal (1/x)
- **in_channel_2**: Name of second channel for channel-to-channel operations. If specified, operation is performed between corresponding elements of two channels.
- **num**: Constant value for channel-to-constant operations. Used when in_channel_2 is not specified.

## Marker Command

Measure time intervals between sequential markers in different channels

The "MARKER" command calculates time intervals between pairs of markers where a marker in the first channel is followed by a marker in the second channel. This is used to measure the latency between two event markers.

### Example

```toml
[[command]]
class_name = "marker"
in = ["experiment_data"]
out = ["reaction_times"]
in_channel = ["STIMULUS_MARKER"]
in_channel_2 = ["RESPONSE_MARKER"]
out_channel = ["REACTION_TIME_SECONDS"]
```

### Explanation of Keys

- **in_channel_2**: Name of the second marker channel

## Morphology Command

Extract and calculate waveform shape features from a specified channel.

The MORPHOLOGY command analyzes the waveform in the input channel and computes various morphological features for each segment or event of interest. This is useful for quantifying the shape, width, amplitude, curvature, and other characteristics of physiological signals like blood velocity signals.

### Example

```toml
[[command]]
class_name = "morphology"
in = "data"
out = "data"
in_channel = "mcav_wave"
out_channel = "morphology"
mask = "mcav_mask"
features = [
    "X",
    "Y",
    "WIDTH_0",
    "WIDTH_25",
    "WIDTH_50",
    "WIDTH_75",
    "PROMINENCE",
    "CURVATURE",
    "SLOPE",
    "INTEGRAL",
    "ANGLE",
    "STATS_Y",
    "STATS_X",
    "AUC",
    "DECAY",
    "VCI"
]
prominence_level = 0.01
```

### Explanation of Keys

- **mask**: Optional channel or array that specifies which segments of the waveform to include in the analysis.
- **features**: List of morphological features to compute.
- **prominence_level**: Threshold for peak prominence when detecting waveform peaks. As a percentage of overall height, so 0.01 means 1%

A full list of acceptable morphological features are:

- _X_: The latency of the 3 peaks and valleys
- _Y_: The height of the 3 peaks and valleys
- _WIDTH_0_: The width at 0% of the prominence of the peak/valley
- _WIDTH_25_: The width at 25% of the prominence of the peak/valley
- _WIDTH_50_:
- _WIDTH_75_:
- _PROMINENCE_: The prominence of the peak/valley
- _CURVATURE_: The curvature at the top/bottom of the peak/valley
- _SLOPE_: The slope between the 2 significant points (peaks and valley)
- _INTEGRAL_: the integral between two significant points
- _ANGLE_: The angle between 3 significant points
- _STATS_Y_: Common statistical values of the overall waveform
- _STATS_X_: Common statistical values of the overall waveform
- _AUC_: The overall area under the curve of the waveform
- _DECAY_: The diastolic decay of the final peak
- _VCI_: The Velocity Curvature Index of the waveform

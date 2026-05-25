"""
Morphology Command - Extract morphological features from physiological waveforms.

This module implements the Morphology command class which analyzes waveform data
to extract comprehensive morphological features including peaks, valleys, widths,
prominences, slopes, integrals, angles, and statistical properties.
"""

import math
from scipy import signal  # Filtering
from statistics import mean, mode, median, stdev, variance
from scipy import stats
import numpy as np

from common import Command, copy_dict, time_from_string


class Morphology(Command):
    """
    Extract morphological features from physiological waveforms.

    The Morphology command analyzes waveform data to extract comprehensive
    morphological features including peaks, valleys, widths, prominences,
    slopes, integrals, angles, and statistical properties. It is particularly
    useful for analyzing physiological signals like PPG, ECG, or other
    oscillatory waveforms.

    Attributes
    ----------
    format : str or list[str]
        List of morphological features to extract. Each feature corresponds
        to a specific waveform characteristic.
    alright : str or list[str]
        Name of the validation channel that indicates which waveforms are
        valid for analysis. Values should be binary (0 = invalid, 1 = valid).
    prominence_level : float
        Minimum prominence threshold for peak/valley detection. Default is 0.05.
        Peaks/valleys with prominence below this threshold are ignored.
    good : bool
        Flag indicating whether the command instance is valid and ready to execute.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize Morphology command instance.

        Parameters
        ----------
        command : dict
            Configuration dictionary containing:

            - "format" : str or list[str]
                List of morphological features to extract
            - "alright" : str or list[str]
                Name of validation channel for waveform validity
            - "prominence_level" : float
                Minimum prominence for peak/valley detection (default: 0.05)
            - Additional parameters inherited from Command base class:
              "name", "resultant", "channel", "out_channel"

        Notes
        -----
        Supported format values:
            - "X": Significant point indices [0, peak1, valley1, peak2, valley2, peak3, end]
            - "Y": Y-values at significant points
            - "WIDTH_0": Peak/valley widths at 100% height (baseline)
            - "WIDTH_25": Peak/valley widths at 75% height
            - "WIDTH_50": Peak/valley widths at 50% height (half-width)
            - "WIDTH_75": Peak/valley widths at 25% height
            - "PROMINENCE": Peak/valley prominence values
            - "CURVATURE": Curvature at significant points
            - "SLOPE": Slopes between consecutive significant points
            - "INTEGRAL": Integrals between consecutive significant points
            - "ANGLE": Angles formed by triplets of consecutive points
            - "STATS_Y": Statistics of Y-values (mean, median, mode, std, variance)
            - "STATS_X": Signal statistics (center of mass, skewness, kurtosis)
            - "AUC": Total area under curve
            - "DECAY": Decay rate from third peak to 30% height
            - "VCI": Velocity Change Index (total curvature)
        """
        super().__init__(command)
        self.format = command.get("features", "")
        self.alright = command.get("mask", "")
        self.prominence_level = command.get("prominence_level", 0.05)

        self.good = False

    def validate(self) -> bool:
        """
        Validate the Morphology instance configuration.

        Performs comprehensive validation including type checking,
        value validation, and base class validation.

        Returns
        -------
        bool
            True if the instance is valid, False otherwise.

        Raises
        ------
        ValueError
            If format values are not recognized or parameter sizes don't match.

        Notes
        -----
        Validation includes:
        1. Type checking for string and numeric parameters
        2. Size consistency across parameter lists
        3. Verification of format values against allowed set
        4. Base class validation
        """
        is_valid = True

        required_str = ["format", "alright"]
        if not self.check_type_inner(required_str, [str]):
            is_valid = False

        required_str = ["prominence_level"]
        if not self.check_type_inner(required_str, [int, float]):
            is_valid = False

        if is_valid:
            self.string_upper(["format", "alright"])

        self.equal_size(["name", "channel", "resultant", "out_channel", "alright"])
        self.equal_size(["format"])

        for form in self.format:
            if form not in [
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
                "VCI",
            ]:
                self.print("error", f"'{form}' is not a valid format for {self.type}")
                is_valid = False

        if not super().validate() or not is_valid:
            self.print("error", f"{self.type} class is not valid")
            return False

        self.print("debug", f"{self.type} class is valid")
        return True

    def execute(self, variables: dict[str, list[dict]]) -> dict[str, list[dict]]:
        """
        Execute the Morphology command on the provided variables.

        Parameters
        ----------
        variables : dict[str, list[dict]]
            Dictionary containing input data variables keyed by variable name.
            Each value is a list of person dictionaries containing waveform data.

        Returns
        -------
        dict[str, list[dict]]
            Dictionary with morphological features added to the output variables.
            Each feature set is stored as a list of flattened feature vectors,
            one vector per waveform.

        Notes
        -----
        - If the command is invalid (self.good is False), returns input unchanged
        - Multiple morphological analyses can be performed simultaneously
          by providing arrays for parameters
        - Features are extracted only for waveforms marked as valid (alright=1)
        - Invalid or insufficient waveforms result in NaN-filled feature vectors
        """
        self.good = self.validate()

        if not self.good:
            print("error", f"{self.type} command invalid, being skipped")
            return variables

        self.print("command", f"Running the {self.type} command")
        for name, channel, resultant, out_channel, alright in zip(
            self.name, self.channel, self.resultant, self.out_channel, self.alright
        ):
            new_people = []
            if name not in variables.keys():
                self.print("error", f"Could not find {name} in {variables.keys()}")
            for person_ in variables.get(name):
                person = copy_dict(person_)
                person = self.morphology(person, channel, out_channel, alright)
                new_people.append(person)
            variables[resultant] = new_people
        return variables

    def morphology(
        self,
        person: dict[str, any],
        channel: str,
        out_channel: str,
        alright: list[bool],
    ) -> dict[str, any]:
        """
        Extract morphological features from waveforms in the specified channel.

        Parameters
        ----------
        person : dict[str, any]
            Dictionary containing person's data with keys:
            - "FILENAME": Source filename
            - channel: List of waveforms to analyze (list of y-value lists)
            - Additional waveform metadata
        channel : str
            Name of the input channel containing waveform data.
        out_channel : str
            Name of the output channel for morphological features.
        alright : list[bool]
            List indicating which waveforms are valid for analysis.

        Returns
        -------
        dict[str, any]
            Updated person dictionary with morphological features stored
            under out_channel. Features are stored as a list of flattened
            feature vectors.

        """
        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                channel_name=channel, out_channel=out_channel, format=self.format
            ),
        )

        person[alright] = self.ensure_alright(person, channel, alright)
        features = []

        if channel not in person:
            self.print("error", f"could not find {channel} in person")

        for N, wave_y in enumerate(person[channel]):
            features_map = {
                "X": [float("nan")] * 7,
                "Y": [float("nan")] * 7,
                "WIDTH_0": [float("nan")] * 5,
                "WIDTH_25": [float("nan")] * 5,
                "WIDTH_50": [float("nan")] * 5,
                "WIDTH_75": [float("nan")] * 5,
                "PROMINENCE": [float("nan")] * 5,
                "CURVATURE": [float("nan")] * 5,
                "SLOPE": [float("nan")] * 6,
                "INTEGRAL": [float("nan")] * 6,
                "ANGLE": [float("nan")] * 5,
                "STATS_Y": [float("nan")] * 5,
                "STATS_X": [float("nan")] * 3,
                "AUC": [float("nan")],
                "DECAY": [float("nan")],
                "VCI": [float("nan")],
            }
            if person[alright][N] == 0:
                features.append(features_map)
                continue
            if len(wave_y) <= 3:
                features.append(features_map)
                continue

            wave_x = np.linspace(0, len(wave_y)/person["FREQUENCY"], num=len(wave_y))
            wave_y = np.array(wave_y)
            wave_y_neg = -np.array(wave_y)  # Precompute negative for valleys
            peaks, peak_properties = signal.find_peaks(
                wave_y, prominence=self.prominence_level
            )
            valleys, valley_properties = signal.find_peaks(
                wave_y_neg, prominence=self.prominence_level
            )
            self.print("index", f"peaks found {peaks}")
            self.print("index", f"valleys found {valleys}")

            peak_proms = peak_properties["prominences"].tolist()
            valley_proms = valley_properties["prominences"].tolist()

            # Peak Widths and Promeinces
            peak_widths = {}
            valley_widths = {}
            relative_heights = [1, 0.75, 0.5, 0.25]
            for h in relative_heights:
                peak_widths_eval = signal.peak_widths(wave_y, peaks, rel_height=h)
                peak_widths[h] = peak_widths_eval[0].tolist()

                valley_widths_eval = signal.peak_widths(
                    wave_y_neg, valleys, rel_height=h
                )
                valley_widths[h] = valley_widths_eval[0].tolist()

            peaks = peaks.tolist()
            valleys = valleys.tolist()

            # Ensure the first valley comes after the first peak
            while valleys and peaks and valleys[0] < peaks[0]:
                valleys.pop(0)
                valley_proms.pop(0)
                for h in relative_heights:
                    valley_widths[h].pop(0)

            # Making sure we have enough waves.
            if len(peaks) < 3 or len(valleys) < 2:
                self.print(
                    "index",
                    f"not enough significant points, valleys:'{len(valleys)}', peaks'{len(peaks)}'",
                )
                features.append(features_map)
                continue

            significant_x = [
                0,
                peaks[0],
                valleys[0],
                peaks[1],
                valleys[1],
                peaks[2],
                len(wave_y) - 1,
            ]
            significant_y = [wave_y[i] for i in significant_x]
            for i in range(1, len(significant_x)):
                if significant_x[i] <= significant_x[i - 1]:
                    self.print(
                        "index",
                        f"Wave{N} into an instance of non ascending order '{significant_x}'",
                    )
                    features.append(features_map)
                    continue
            significant_x_time = [0,0,0,0,0,0,0]
            for i,val in enumerate(significant_x):
                significant_x_time[i] = val/person["FREQUENCY"]


            # If we are here, we assume we are dealing with a most likely valid wave
            # Calculating Values
            width_00 = [
                peak_widths[1][0],
                valley_widths[1][0],
                peak_widths[1][1],
                valley_widths[1][1],
                peak_widths[1][2],
            ]
            width_25 = [
                peak_widths[0.75][0],
                valley_widths[0.75][0],
                peak_widths[0.75][1],
                valley_widths[0.75][1],
                peak_widths[0.75][2],
            ]
            width_50 = [
                peak_widths[0.5][0],
                valley_widths[0.5][0],
                peak_widths[0.5][1],
                valley_widths[0.5][1],
                peak_widths[0.5][2],
            ]
            width_75 = [
                peak_widths[0.25][0],
                valley_widths[0.25][0],
                peak_widths[0.25][1],
                valley_widths[0.25][1],
                peak_widths[0.25][2],
            ]
            prom = [
                peak_proms[0],
                valley_proms[0],
                peak_proms[1],
                valley_proms[1],
                peak_proms[2],
            ]

            if len(wave_y) < 3:
                VCI = 0.0
            else:
                VCI = sum(float(self.curvature(wave_y, j)) for j in range(len(wave_y)))

            features_map = {
                "X": significant_x_time,
                "Y": [float(item) for item in significant_y],
                "WIDTH_0": width_00,
                "WIDTH_25": width_25,
                "WIDTH_50": width_50,
                "WIDTH_75": width_75,
                "PROMINENCE": prom,
                "CURVATURE": [
                    float(self.curvature(wave_y, significant_x[j])) for j in range(1, 6)
                ],
                "SLOPE": [
                    float(
                        (significant_y[j] - significant_y[j - 1])
                        / (significant_x_time[j] - significant_x_time[j - 1])
                    )
                    for j in range(1, 7)
                ],
                "INTEGRAL": [
                    float(self.integral(wave_y, significant_x[j - 1], significant_x[j]))
                    for j in range(1, 7)
                ],
                "ANGLE": [
                    float(
                        self.angle(
                            (significant_x[j - 1], significant_y[j - 1]),
                            (significant_x[j], significant_y[j]),
                            (significant_x[j + 1], significant_y[j + 1]),
                        )
                    )
                    for j in range(1, 6)
                ],
                "STATS_Y": [
                    float(mean(wave_y)),
                    float(median(wave_y)),
                    float(mode(wave_y)),
                    float(stdev(wave_y)),
                    float(variance(wave_y)),
                ],
                "STATS_X": [
                    float(self.center_of_mass(wave_y)),
                    float(stats.skew(wave_y)),
                    float(stats.kurtosis(wave_y)),
                ],
                "AUC": [float(self.integral(wave_y, 0, len(wave_y)))],
                "DECAY": float(self.decay(wave_y, peaks, 3, height=0.3)),
                "VCI": VCI,
            }
            features.append(features_map)

        person_features = []
        for features_wave in features:
            wave_features = []
            for form in self.format:
                if form in features_wave:
                    wave_features.append(features_wave[form])
            flat_list = []
            for item in wave_features:
                if isinstance(item, list):
                    flat_list.extend(item)  # Unpack lists
                else:
                    flat_list.append(item)  # Append single values
            person_features.append(flat_list)

        person[out_channel] = person_features
        return person

    def center_of_mass(self, signal: list[float]) -> float:
        """
        Calculate the center of mass (weighted average position) of a signal.

        Parameters
        ----------
        signal : list[float]
            The signal values.

        Returns
        -------
        float
            Center of mass position. Returns 0 if signal is empty or total mass is zero.

        Notes
        -----
        The center of mass is calculated as:
        COM = Σ(i * signal[i]) / Σ(signal[i])
        where i is the index position.
        """
        if len(signal) == 0:
            self.print("index", "signal is empty, returning 0")
            return 0
        total_mass = sum(signal)
        if total_mass == 0:
            self.print("index", "Mass of signal is zero, returning 0")
            return 0

        weighted_sum = sum(i * signal[i] for i in range(len(signal)))
        return weighted_sum / total_mass

    def integral(self, data, a, b):
        """
        Calculate the approximate integral (sum) of data between indices a and b.

        Parameters
        ----------
        data : list[float]
            The signal data.
        a : int
            Starting index (inclusive).
        b : int
            Ending index (exclusive).

        Returns
        -------
        float
            Sum of data values between indices a and b.
        """
        return sum(data[a:b])

    def angle(self, a, b, c):
        """
        Calculate the angle formed by three points a, b, and c at vertex b.

        Parameters
        ----------
        a : tuple[float, float]
            First point (x, y).
        b : tuple[float, float]
            Vertex point (x, y).
        c : tuple[float, float]
            Third point (x, y).

        Returns
        -------
        float
            Angle in radians at vertex b.

        Notes
        -----
        Calculates angle using dot product formula:
        cos(θ) = (AB·BC) / (|AB| * |BC|)
        where AB = b - a, BC = c - b
        """
        AB = (b[0] - a[0], b[1] - a[1])
        BC = (c[0] - b[0], c[1] - b[1])

        dot_product = AB[0] * BC[0] + AB[1] * BC[1]

        magnitude_AB = math.sqrt(AB[0] ** 2 + AB[1] ** 2)
        magnitude_BC = math.sqrt(BC[0] ** 2 + BC[1] ** 2)

        cos_angle = dot_product / (magnitude_AB * magnitude_BC)
        angle_radians = math.acos(cos_angle)

        return angle_radians

    def curvature(self, signal, x):
        """
        Calculate the curvature of a signal at a specific point.

        Parameters
        ----------
        signal : list[float]
            The signal values.
        x : int
            Index at which to calculate curvature.

        Returns
        -------
        float
            Curvature value at point x. Returns 0 for boundary points.

        Notes
        -----
        Curvature is approximated using finite differences:
        κ = |y''| / (1 + (y')²)^(3/2)
        where y' and y'' are first and second derivatives.
        """
        if x <= 0 or x >= len(signal) - 1:
            return 0

        first_derivative = signal[x] - signal[x - 1]
        # second_derivative = (signal[x] - signal[x - 1]) - (
        #    signal[x - 1] - signal[x - 2]
        # )
        second_derivative = signal[x + 1] - 2 * signal[x] + signal[x - 1]
        curvature = abs(second_derivative) / (1 + first_derivative**2) ** (3 / 2)

        return curvature

    def decay(self, data, peaks, peak_n, height=0.3):
        """
        Calculate the decay rate from a specified peak to a percentage of its height.

        Parameters
        ----------
        data : list[float]
            The signal data.
        peaks : list[int]
            Indices of detected peaks.
        peak_n : int
            Index of the peak to analyze (0-based).
        height : float, optional
            Target height as percentage of peak value (default: 0.3 = 30%).

        Returns
        -------
        float
            Decay rate defined as (peak_value - target_value) / decay_distance.
            Returns 0.0 if peak index is invalid.
        """
        if peak_n >= len(peaks) or peak_n < 0:
            return 0.0  # Return zero if the peak index is invalid

        peak_index = peaks[peak_n]
        peak_value = data[peak_index]
        target_value = peak_value * height

        # Start searching for the decay point after the peak
        for i in range(peak_index + 1, len(data)):
            if data[i] <= target_value:
                # Calculate decay rate: (peak_value - target_value) / decay distance
                decay_distance = i - peak_index
                decay_rate = (peak_value - data[i]) / decay_distance
                return decay_rate

        # If no decay point is found within the signal range
        # Return decay rate considering the last point in the data
        decay_distance = len(data) - 1 - peak_index
        decay_rate = (
            (peak_value - data[len(data) - 1]) / decay_distance
            if decay_distance > 0
            else 0.0
        )
        return decay_rate

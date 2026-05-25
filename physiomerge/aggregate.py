"""
Aggregate Command Module

This module provides the Aggregate class for performing statistical aggregation
operations on time-series data channels with optional masking and weighting.
"""

import numpy as np
from scipy.stats import mode

from common import Command, copy_dict, time_from_string


class Aggregate(Command):
    """
    Aggregate Command - Statistical aggregation with optional masking and weighting.

    Performs various statistical aggregations on data channels with support for
    data filtering via masks and weighted calculations. Each aggregation operation
    is applied to the specified channel data, with optional filtering based on
    a mask channel and weighting using a weights channel.

    Attributes
    ----------
    format : str
        Type of statistical aggregation to perform. Must be one of:
        "mean", "variance", "std", "min", "max", "median", "mode"
    alright : str
        Name of the mask channel used for filtering data (internally named).
    weights : str
        Name of the channel containing weights for weighted calculations.
    good : bool
        Validation status indicating whether the command is properly configured.
    """

    def __init__(self, command: dict) -> None:
        """
        Initialize an Aggregate command instance.

        Parameters
        ----------
        command : dict
            Configuration dictionary containing:

            - "format" : str
                Type of aggregation to perform
            - "mask" : str
                Mask channel name (stored internally as 'alright')
            - "weights" : str
                Weights channel name
            - "outlier" : str
                determines the type of outlier removal to use
            - "outlier_num" : float/int
                The number to use for outlier removal
        """
        super().__init__(command)
        self.format = command.get("format", "").lower()
        self.alright = command.get("mask", "")
        self.weights = command.get("weights", "")
        self.outlier_type = command.get("outlier", "none").lower()
        self.outlier_val = command.get("outlier_num", 0)

        self.good = self.validate()

    def validate(self) -> bool:
        """
        Validate the Aggregate instance configuration.

        Performs comprehensive validation including type checking, format validation,
        size consistency checks, and base class validation.

        Returns
        -------
        bool
            True if the instance is valid, False otherwise.

        Notes
        -----
        Validation includes:
        1. Type checking for string parameters
        2. Format validation against allowed aggregation types
        3. Size consistency across parameter lists
        4. Base class validation
        """
        is_valid = True

        required_str = ["format", "alright", "weights", "outlier_type"]
        if not self.check_type_inner(required_str, [str]):
            is_valid = False

        required_int = ["outlier_val"]
        if not self.check_type_inner(required_int, [int, float, None]):
            is_valid = False

        if is_valid:
            self.string_upper(["alright", "weights"])

        # Validate format
        valid_formats = {
            "mean",
            # "weighted_mean", this is no longer an option, its default for mean now.
            "variance",
            "std",
            "min",
            "max",
            "difference",
            "median",
            "mode",
        }
        if not self.is_in_array(self.format, valid_formats):
            is_valid = False

        valid_formats = {
            "z_transform",  # Z transform
            "mad",  # Median Absolute Deviation
            "iqr",  # Interquatile Range
            "none",
        }
        if not self.is_in_array(self.outlier_type, valid_formats):
            is_valid = False

        # ensure specified attributes have matching sizes
        try:
            self.equal_size(
                [
                    "name",
                    "resultant",
                    "channel",
                    "alright",
                    "out_channel",
                    "weights",
                    "outlier_type",
                    "outlier_val",
                    "format",
                ]
            )
        except ValueError as e:
            self.print("error", f"Validation failed: {e}")
            is_valid = False

        # Validate using the base class
        if not super().validate() or not is_valid:
            self.print("error", f"{self.type} class is not valid")
            return False

        self.print("debug", f"{self.type} class is valid")
        return True

    def execute(
        self, variables: dict[str, list[dict[str, any]]]
    ) -> dict[str, list[dict[str, any]]]:
        """
        Execute the Aggregate command on the provided variables.

        Parameters
        ----------
        variables : dict[str, list[dict[str, any]]]
            Dictionary containing input data variables keyed by variable name.
            Each value is a list of person dictionaries containing:
            - "FILENAME": Unique identifier for the person/recording
            - Channel data as lists of segments
            - Optional mask and weight channels

        Returns
        -------
        dict[str, list[dict[str, any]]]
            Dictionary with aggregated results added to the output variables.
            Each result is stored as a single-element list containing the aggregated
            value(s) for each person.

        Notes
        -----
        - If the command is invalid (self.good is False), returns input unchanged
        - For weighted operations, the weighted mean is calculated using numpy's
          average function with weights
        - Empty filtered data results in NaN values
        - NaN values in data are handled appropriately for each aggregation type
        """
        self.good = self.validate()
        if not self.good:
            self.print("warning", f"{self.type} command invalid, being skipped")
            return variables

        self.print(
            "command", f"Running the {self.type} command in format '{self.format}'"
        )

        for (
            name,
            resultant,
            channel,
            out_channel,
            alright,
            weight,
            outlier,
            outlier_val,
            format,
        ) in zip(
            self.name,
            self.resultant,
            self.channel,
            self.out_channel,
            self.alright,
            self.weights,
            self.outlier_type,
            self.outlier_val,
            self.format,
        ):
            new_people = []
            for person_ in variables.get(name):
                person = copy_dict(person_)
                person = self.aggregate_data(
                    person,
                    channel,
                    out_channel,
                    format,
                    alright,
                    weight,
                    outlier,
                    outlier_val,
                )
                new_people.append(person)
            variables[resultant] = new_people

        return variables

    def aggregate_data(
        self,
        person: dict[str, any],
        channel: str,
        out_channel: str,
        format: str,
        alright: str,
        weight: str,
        outlier: str,
        outlier_val: any,
    ) -> dict[str, any]:
        """
        Aggregate data for a single person.

        Parameters
        ----------
        person : dict[str, any]
            Dictionary containing person's data channels.
            Expected to contain:
            - "FILENAME": Source filename
            - channel: List of data segments to aggregate
            - alright: List of mask values (1=include, 0=exclude)
            - weight: List of weight values for weighted calculations
        channel : str
            Name of the input channel to aggregate.
        out_channel : str
            Name of the output channel for aggregated result.
        alright : str
            Name of the mask channel for filtering data.
        weight : str
            Name of the channel containing weights.

        Returns
        -------
        dict[str, any]
            Updated person dictionary with aggregated result added to out_channel.
            The result is stored as a single-element list containing the aggregated
            value(s).

        Notes
        -----
        - Data is filtered using the mask channel: only segments where mask=1 are used
        - Weighted mean is the default for "mean" format
        - NaN values are handled appropriately for each aggregation type
        - If filtered data is empty, result is NaN
        - Mode calculation uses scipy.stats.mode with NaN values omitted
        """

        def weighted_mean_nan(data, weights):
            """
            Calculate weighted mean while handling NaN values.

            Parameters
            ----------
            data : np.ndarray
                Input data array.
            weights : np.ndarray
                Weights array.

            Returns
            -------
            list
                List containing the weighted mean as a float.

            Notes
            -----
            - Only valid (non-NaN) data and weights are used in calculation
            - Returns NaN if no valid data/weight pairs exist
            """
            # Ensure numpy arrays
            data = np.asarray(data) if data is not None else None
            weights = np.asarray(weights) if weights is not None else None

            # Handle None or empty inputs
            if data is None or data.size == 0:
                data = np.array([[float("nan")]])

            if weights is None or weights.size == 0:
                weights = np.array([[float("nan")]])

            # Remove rows containing NaNs
            valid_mask = ~(np.isnan(data).any(axis=1) | np.isnan(weights).any(axis=1))

            if not np.any(valid_mask):
                return float("nan")  # no valid data at all
            
            data = data[valid_mask]
            weights = weights[valid_mask]
            weights = np.broadcast_to(weights, data.shape)
            
            out = np.average(data, axis=0, weights=weights)
            out = out.tolist()
            return out

        def outlier_z(data, mask, threshold=3):
            data = np.array(data)
            outliers = np.zeros(len(data), dtype=bool)
            for j in range(data.shape[1]):
                col = data[:, j]
                z_scores = (col - np.mean(col)) / np.std(col)
                outliers |= np.abs(z_scores) > threshold

            return [mask[i] & (not outliers[i]) for i in range(len(mask))]

        def outlier_mad(data, mask, threshold=3.5):
            data = np.array(data)
            outliers = np.zeros(len(data), dtype=bool)

            for j in range(data.shape[1]):
                col = data[:, j]
                median = np.median(col)
                mad = np.median(np.abs(col - median))
                modified_z_scores = 0.6745 * (col - median) / mad
                outliers |= np.abs(modified_z_scores) > threshold

            return [mask[i] & (not outliers[i]) for i in range(len(mask))]

        def outlier_iqr(data, mask, threshold=1.5):
            data = np.array(data)
            outliers = np.zeros(len(data), dtype=bool)

            for j in range(data.shape[1]):
                col = data[:, j]
                q1, q3 = np.percentile(col, [25, 75])
                iqr = q3 - q1
                lower = q1 - threshold * iqr
                upper = q3 + threshold * iqr
                outliers |= (col < lower) | (col > upper)

            return [mask[i] & (not outliers[i]) for i in range(len(mask))]

        def outlier_none(data, mask):
            return mask

        self.print(
            "debug",
            f"{self.type} of {person["FILENAME"]} - ",
            self.debug_data(
                channale_name=channel,
                out_channel=out_channel,
                alright_mask=alright,
                format=format,
                outlier=outlier,
            ),
        )

        # Filter the data using 'alright' mask
        if channel not in person.keys():
            self.print(
                "debug", f"Person does not contain '{channel}' in their {person.keys()}"
            )
            return person

        person[alright] = self.ensure_alright(person, channel, alright)
        person_weights = self.ensure_channel(person, channel, weight)

        if not person[channel]:
            self.print("warning", f"Empty channel for {person['FILENAME']}")

        if outlier_val == 0:
            outlier_val = None
        # Outlier Removal
        outlier_function = {
            "z_transform": lambda data, mask: outlier_z(
                data, mask, outlier_val if outlier_val else 3
            ),
            "mad": lambda data, mask: outlier_mad(
                data, mask, outlier_val if outlier_val else 3.5
            ),
            "iqr": lambda data, mask: outlier_iqr(
                data, mask, outlier_val if outlier_val else 1.5
            ),
            "none": lambda data, mask: outlier_none(data, mask),
        }
        if person[alright]:
            person[alright] = outlier_function[outlier](person[channel], person[alright])

        filtered_data = [d for a, d in zip(person[alright], person[channel]) if a == 1]
        filtered_weights = [
            d for a, d in zip(person[alright], person_weights) if a == 1
        ]
        data_array = np.array(filtered_data)
        data_weights = np.array(filtered_weights)

        if len(filtered_data) == 0:
            self.print(
                "warning", f"Filtered data array was empty for {person['FILENAME']}"
            )
            result = [[float("NaN")]]
        else:
            self.print("debug", f"Filtered length {len(filtered_data)}")

            # Mapping aggregate functions
            aggregate_functions = {
                "mean": lambda data: weighted_mean_nan(data, data_weights),
                "variance": lambda data: np.nanvar(data, axis=0).tolist(),
                "std": lambda data: np.nanstd(data, axis=0).tolist(),
                "min": lambda data: np.nanmin(data, axis=0).tolist(),
                "max": lambda data: np.nanmax(data, axis=0).tolist(),
                "difference": lambda data: (np.nanmax(data, axis=0) - np.nanmin(data, axis=0)).tolist(),
                "median": lambda data: np.nanmedian(data, axis=0).tolist(),
                "mode": lambda data: mode(data, axis=0, nan_policy="omit")
                .mode[0]
                .tolist(),
            }

            # Apply the appropriate function
            result = [aggregate_functions[format](data_array)]

        # Append the result back to the person
        person[out_channel] = result
        return person

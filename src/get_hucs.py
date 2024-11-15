import pandas as pd
import numpy as np


def get_hucs(level="huc10", sample_size=None, random_seed=None, filter_prefix=None):
    """
    Get HUC IDs at specified level with optional sampling and filtering.

    Parameters
    ----------
    level : str
        HUC level to process. Options: 'huc8', 'huc10', 'huc12'
    sample_size : int, optional
        Number of HUCs to randomly sample. If None, returns all matching HUCs
    random_seed : int, optional
        Random seed for reproducible sampling. Only used if sample_size is specified
    filter_prefix : str, optional
        Filter HUCs by prefix (e.g., '1805' for California region)

    Returns
    -------
    list
        List of HUC IDs meeting the specified criteria

    Examples
    --------
    >>> get_hucs('huc8', sample_size=5, random_seed=42, filter_prefix='1805')
    >>> get_hucs('huc10', filter_prefix='18')
    >>> get_hucs('huc12', sample_size=10)
    """

    # Validate level
    valid_levels = {
        "huc8": 8,
        "huc10": 10,
        "huc12": 12,
    }
    if level not in valid_levels:
        raise ValueError(
            f"Invalid HUC level. Must be one of {list(valid_levels.keys())}"
        )

    # Read HUC data
    try:
        hucs = pd.read_csv("huc10s.csv")  # Assuming this is your base data file
    except FileNotFoundError:
        raise FileNotFoundError(
            "HUC data file not found. Please ensure 'huc10s.csv' exists."
        )

    # Extract HUC column
    huc_col = "huc10"  # Adjust if your column name is different
    if huc_col not in hucs.columns:
        raise ValueError(f"Column '{huc_col}' not found in data file")

    # Convert HUCs to requested level
    level_length = valid_levels[level]
    hucs["processed_huc"] = hucs[huc_col].str[:level_length]

    # Remove duplicates after truncating to requested level
    hucs = hucs["processed_huc"].drop_duplicates()

    # Apply filter if specified
    if filter_prefix:
        if not isinstance(filter_prefix, str) or not filter_prefix.isdigit():
            raise ValueError("filter_prefix must be a string of digits")
        hucs = hucs[hucs.str.startswith(filter_prefix)]

        if hucs.empty:
            raise ValueError(f"No HUCs found with prefix '{filter_prefix}'")

    # Convert to list
    hucs = hucs.tolist()

    # Apply sampling if specified
    if sample_size is not None:
        if not isinstance(sample_size, int) or sample_size < 1:
            raise ValueError("sample_size must be a positive integer")
        if sample_size > len(hucs):
            raise ValueError(
                f"sample_size ({sample_size}) is larger than available HUCs ({len(hucs)})"
            )

        # Set random seed if specified
        if random_seed is not None:
            np.random.seed(random_seed)

        hucs = np.random.choice(hucs, size=sample_size, replace=False).tolist()

    return sorted(hucs)  # Return sorted list for consistency


# Example usage in Snakefile:
def get_huc_ids_from_config(config):
    """
    Get HUC IDs based on configuration settings.

    Expected config parameters:
    - huc_ids: Optional list of specific HUC IDs to process
    - huc_level: HUC level to process (e.g., 'huc10')
    - huc_filter: Optional prefix to filter HUCs
    - sample_size: Optional number of HUCs to sample
    - random_seed: Optional random seed for sampling
    """
    if "huc_ids" in config:
        return config["huc_ids"]

    return get_hucs(
        level=config.get("huc_level", "huc10"),
        sample_size=config.get("sample_size"),
        random_seed=config.get("random_seed"),
        filter_prefix=config.get("huc_filter"),
    )

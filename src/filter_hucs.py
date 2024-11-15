"""
filter_huc_list
"""
import pandas as pd
import numpy as np


def filter_huc_list(manifest, level, sample_size=None, random_seed=None, filter_prefix=None):

    # filter by level
    hucs = manifest.loc[manifest['level'] == level, 'hucid']
    hucs = hucs.astype(str)

    # Apply prefix filter if specified
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

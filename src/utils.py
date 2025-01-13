import numpy as np
import pandas as pd


def filter_huc10_list(hucs, prefix=None, sample_size=None, random_seed=None):
    if prefix is not None:
        hucs = hucs[hucs.str.startswith(prefix)]
        if len(hucs) == 0:
            raise ValueError(f"No HUCs found with prefix '{prefix}'")

    if random_seed is not None:
        np.random.seed(random_seed)

    if sample_size is not None:
        hucs = np.random.choice(hucs, size=sample_size, replace=False)

    return hucs.to_list()


def get_target_hucs(config):
    if "huc_id" in config:
        return [str(config["huc_id"])]

    if "huc_ids" in config:
        return [str(huc) for huc in config["huc_ids"]]

    if "huc_manifest" in config:
        df = pd.read_csv(config["huc_manifest"])
        hucs = df["hucid"]

        prefix = config.get("prefix")
        sample_size = config.get("sample_size")
        random_seed = config.get("random_seed")

        return filter_huc10_list(hucs, prefix, sample_size, random_seed)

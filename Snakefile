# Snakefile
import os
from pathlib import Path
import pandas as pd
import numpy as np
import yaml
from typing import List

# Load configuration
configfile: "config.yaml"

# Set default values if not in config
config.setdefault('output_base', '../outputs/')
config.setdefault('params_file', 'configs/params_10m.toml')

# Ensure output base directory exists
output_base = Path(config['output_base'])
output_base.mkdir(parents=True, exist_ok=True)

# Disable HyRiver cache if specified
if config.get('disable_hyriver_cache', True):
    os.environ["HYRIVER_CACHE_DISABLE"] = "true"

def get_hucs(level='huc10', sample_size=None, random_seed=None, filter_prefix=None) -> List[str]:
    """
    Get HUC IDs at specified level with optional sampling and filtering.
    
    Parameters
    ----------
    level : str
        HUC level to process. Options: 'huc6', 'huc8', 'huc10', 'huc12'
    sample_size : int, optional
        Number of HUCs to randomly sample. If None, returns all matching HUCs
    random_seed : int, optional
        Random seed for reproducible sampling. Only used if sample_size is specified
    filter_prefix : str, optional
        Filter HUCs by prefix (e.g., '1805' for California Bay Area region)
    """
    
    valid_levels = {'huc6': 6, 'huc8': 8, 'huc10': 10, 'huc12': 12}
    if level not in valid_levels:
        raise ValueError(f"Invalid HUC level. Must be one of {list(valid_levels.keys())}")
    
    try:
        hucs_df = pd.read_csv("data/huc_manifest/huc_manifest.csv")
        hucs = hucs_df['hucid'].loc[hucs_df['level'] == level].astype(str)
    except FileNotFoundError:
        raise FileNotFoundError(f"HUC data file not found. Please ensure 'data/huc_manifest/huc_manifest.csv' exists. Run scripts/download_huc_manifest.py")
    
    # Apply filter if specified
    if filter_prefix:
        if not isinstance(filter_prefix, str) or not filter_prefix.isdigit():
            raise ValueError("filter_prefix must be a string of digits")
        hucs = hucs[hucs.str.startswith(filter_prefix)]
        
        if len(hucs) == 0:
            raise ValueError(f"No HUCs found with prefix '{filter_prefix}'")
    
    # Apply sampling if specified
    if sample_size is not None:
        if not isinstance(sample_size, int) or sample_size < 1:
            raise ValueError("sample_size must be a positive integer")
        if sample_size > len(hucs):
            raise ValueError(f"sample_size ({sample_size}) is larger than available HUCs ({len(hucs)})")
        
        # Set random seed if specified
        if random_seed is not None:
            np.random.seed(random_seed)
        
        hucs = np.random.choice(hucs, size=sample_size, replace=False)
    
    return sorted(hucs.tolist())

def get_target_hucs() -> List[str]:
    """
    Determine which HUCs to process based on config settings.
    Supports three modes:
    1. Single HUC ID
    2. List of HUC IDs
    3. HUC level with optional filtering and sampling
    """
    # Check for single HUC ID
    if 'huc_id' in config:
        return [str(config['huc_id'])]
    
    # Check for list of HUC IDs
    if 'huc_ids' in config:
        return [str(huc) for huc in config['huc_ids']]
    
    # Check for HUC level configuration
    if 'huc_level' in config:
        return get_hucs(
            level=config['huc_level'],
            sample_size=config.get('sample_size'),
            random_seed=config.get('random_seed'),
            filter_prefix=config.get('huc_filter')
        )
    
    raise ValueError("No valid HUC configuration found. Please specify either 'huc_id', 'huc_ids', or 'huc_level' in config.yaml")

# Get target HUCs based on configuration
try:
    HUCIDS = get_target_hucs()
    print(f"Processing {len(HUCIDS)} HUCs: {HUCIDS}")
except Exception as e:
    print(f"Error determining HUCs to process: {e}")
    raise

# Common output paths
def get_output_paths(wildcards, prefix=""):
    return {
        'dem_raw': f"{output_base}/{prefix}{wildcards.hucid}/{wildcards.hucid}-dem_raw.tif",
        'flowlines_raw': f"{output_base}/{prefix}{wildcards.hucid}/{wildcards.hucid}-flowlines_raw.shp",
        'dem': f"{output_base}/{prefix}{wildcards.hucid}/{wildcards.hucid}-dem.tif",
        'flowlines': f"{output_base}/{prefix}{wildcards.hucid}/{wildcards.hucid}-flowlines.shp",
        'floors': f"{output_base}/floors/{wildcards.hucid}-floors.tif",
        'flowlines_out': f"{output_base}/floors/{wildcards.hucid}-flowlines.shp",
        'wp': f"{output_base}/floors/{wildcards.hucid}-wp.shp",
        'log': f"{output_base}/floors/{wildcards.hucid}-run.log",
        'working_dir': f"{output_base}/{prefix}{wildcards.hucid}_working_dir"
    }

## Rules

rule all:
    input:
        expand(output_base / "floors" / "{hucid}-floors.tif", hucid=HUCIDS)

rule download_data:
    params:
        hucid = '{hucid}'
    output:
        dem = output_base / "{hucid}/{hucid}-dem_raw.tif",
        flowlines = output_base / "{hucid}/{hucid}-flowlines_raw.shp"
    shell:
        "poetry run python src/download_huc.py {params.hucid} {output.dem} {output.flowlines}"

rule preprocess_dem:
    input:
        dem_path = output_base / "{hucid}/{hucid}-dem_raw.tif",
        land_shapefile = "data/california_mask/California.shp"
    output:
        output_base / "{hucid}/{hucid}-dem.tif"
    shell:
        "poetry run python src/ocean_mask.py {input.dem_path} {input.land_shapefile} {output}"

rule preprocess_nhd:
    input:
        output_base / "{hucid}/{hucid}-flowlines_raw.shp"
    output:
        output_base / "{hucid}/{hucid}-flowlines.shp"
    shell:
        "poetry run python src/filter_nhd.py {input} {output}"

rule extract_valleys:
    input:
        dem = output_base / "{hucid}/{hucid}-dem.tif",
        network = output_base / "{hucid}/{hucid}-flowlines.shp"
    params:
        param_file = lambda wildcards: config['params_file'],
        working_dir = lambda wildcards: get_output_paths(wildcards)['working_dir'],
        flowlines_ofile = lambda wildcards: get_output_paths(wildcards)['flowlines_out'],
        wp_ofile = lambda wildcards: get_output_paths(wildcards)['wp'],
        log_file = lambda wildcards: get_output_paths(wildcards)['log']
    output:
        output_base / "floors/{hucid}-floors.tif"
    shell:
        """
        poetry run python -m valleyx \
            --dem_file {input.dem} \
            --flowlines_file {input.network} \
            --working_dir {params.working_dir} \
            --param_file {params.param_file} \
            --floor_ofile {output} \
            --flowlines_ofile {params.flowlines_ofile} \
            --wp_ofile {params.wp_ofile} \
            --enable_logging \
            --log_file {params.log_file}
         """

## End of Snakefile

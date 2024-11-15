# Snakefile
import os
from pathlib import Path
import pandas as pd
import yaml

# Load configuration
configfile: "config.yaml"

# Set default values if not in config
config.setdefault('output_base', '../outputs/')
config.setdefault('random_seed', 14)
config.setdefault('sample_size', 5)
config.setdefault('params_file', 'configs/params_10m.toml')

# Ensure output base directory exists
output_base = Path(config['output_base'])
output_base.mkdir(parents=True, exist_ok=True)

# Disable HyRiver cache if specified
if config.get('disable_hyriver_cache', True):
    os.environ["HYRIVER_CACHE_DISABLE"] = "true"

# Load and process HUC IDs
def get_huc_ids():
    if 'huc_ids' in config:
        return config['huc_ids']
    else:
        huc10s = pd.read_csv("huc10s.csv")['huc10']
        return list(huc10s.sample(config['sample_size'], 
                                random_state=config['random_seed']))

HUCIDS = get_huc_ids()

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
        land_shapefile = "california_mask/California.shp"
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

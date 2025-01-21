from pathlib import Path 
import json
from typing import List
import os

# Default configuration with option to override via --config
OUTPUT_DIR = Path(config.get("output_dir", "./output"))
HUCS_FILE = Path(config.get("hucs_file", "./data/target_huc10s.csv"))
PARAMS_FILE = Path(config.get("params_file", "./params/params_10m.toml"))

# helper function used in download_all and process_all
def get_hucs() -> List[str]:
    import pandas as pd 
    # if file exists
    if os.path.exists(HUCS_FILE):
        return pd.read_csv(HUCS_FILE)['hucid'].tolist()
    else:
       return []

# WORKFLOW
# 1. Setup
# 2. Download
# 3. Process
# 4. Postprocess (mosaic)

# setup
rule setup:
    output:
        na_boundaries = "data/north_america.shp",
        us_boundaries = "data/us_states.shp",
        whitebox_init = "data/whitebox_init.txt",
    run:
      shell("poetry run python src/dl_land_shape.py")
      shell("poetry run python src/init_whitebox.py")

rule generate_targets:
    output:
        target_huc10s = "data/target_huc10s.csv",
    run:
      shell("poetry run python src/generate_target_huc10s.py")
        
# download
rule download:
    input:
        expand(
            [OUTPUT_DIR / "{hucid}/{hucid}-dem.tif",
             OUTPUT_DIR / "{hucid}/{hucid}-flowlines.shp"],
            hucid=get_hucs()
        )

# process
rule process:
    input:
        expand(
             OUTPUT_DIR / "floors" / "{hucid}-floors.tif",
            hucid=get_hucs()
        )

# postprocess
# TODO: mosaic to state bounds and to watershed bounds


rule download_one:
    input:
        us_land_file = "data/us_states.shp",
        na_land_file = "data/north_america.shp"
    output:
        dem = OUTPUT_DIR / "{hucid}/{hucid}-dem.tif",
        flowlines = OUTPUT_DIR / "{hucid}/{hucid}-flowlines.shp",
    resources:
        download_slots=1
    shell:
        "poetry run python src/dl_dem_and_flowlines.py "
        "{wildcards.hucid} {output.dem} {output.flowlines} "
        "{input.us_land_file} {input.na_land_file}"

rule process_one:
    input:
        dem = OUTPUT_DIR / "{hucid}/{hucid}-dem.tif",
        flowlines = OUTPUT_DIR / "{hucid}/{hucid}-flowlines.shp",
        whitebox_init = "data/whitebox_init.txt"
    params:
        param_file = PARAMS_FILE,
        working_dir = OUTPUT_DIR / "{hucid}/{hucid}_working_dir",
        wp_ofile = OUTPUT_DIR / "{hucid}/{hucid}-wp.shp",
        log_ofile = OUTPUT_DIR / "{hucid}/{hucid}-run.log",
    output:
        valleys = OUTPUT_DIR / "floors" / "{hucid}-floors.tif"
    shell:
        """
        "poetry run python -m valleyx \
        --dem_file {input.dem} \
        --flowlines_file {input.flowlines} \
        --param_file {params.param_file} \
        --wp_ofile {params.wp_ofile} \
        --enable_logging \
        --log_ofile {params.log_ofile} \
        --floor_ofile {output.valleys}
        """

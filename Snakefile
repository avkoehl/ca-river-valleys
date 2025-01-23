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
rule mosaic:
    input:
        floors = expand(OUTPUT_DIR / "floors" / "{hucid}-floors.tif", hucid=get_hucs()),
        us_land_file = "data/us_states.shp",
        na_land_file = "data/north_america.shp"
    output:
        directory(OUTPUT_DIR / "mosaic_ca_watershed"),
        directory(OUTPUT_DIR / "mosaic_ca_state"),
        directory(OUTPUT_DIR / "mosaic_all"),
    shell:
        """
        mkdir -p {output}
        poetry run python src/mosaic.py {OUTPUT_DIR}/floors {OUTPUT_DIR}/mosaic_ca_state {input.na_land_file} {input.us_land_file} --state-boundary-clip --level huc6
        poetry run python src/mosaic.py {OUTPUT_DIR}/floors {OUTPUT_DIR}/mosaic_ca_watershed {input.na_land_file} {input.us_land_file} --watershed-boundary-clip --level huc6
        poetry run python src/mosaic.py {OUTPUT_DIR}/floors {OUTPUT_DIR}/mosaic_all {input.na_land_file} {input.us_land_file} --level huc6
        """

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
        whitebox_init = "data/whitebox_init.txt",
    params:
        working_dir = lambda wildcards: OUTPUT_DIR / f"{wildcards.hucid}_working_dir",
        param_file = PARAMS_FILE,
    output:
        floor_ofile = OUTPUT_DIR / "floors" / "{hucid}-floors.tif",
        wp_ofile = OUTPUT_DIR / "floors" / "{hucid}-wp.shp",
        flowlines_ofile = OUTPUT_DIR / "floors" / "{hucid}-flowlines.shp",
        log_file = OUTPUT_DIR / "floors" / "{hucid}-run.log"
    shell:
        """
        poetry run python -m valleyx \
        --dem_file {input.dem} \
        --flowlines_file {input.flowlines} \
        --param_file {params.param_file} \
        --working_dir {params.working_dir} \
        --wp_ofile {output.wp_ofile} \
        --flowlines_ofile {output.flowlines_ofile} \
        --enable_logging \
        --log_file {output.log_file} \
        --floor_ofile {output.floor_ofile} 
        """

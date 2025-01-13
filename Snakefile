# Snakefile
# poetry run snakemake all --configfile config.yaml -j 1 -n
from pathlib import Path

from src.utils import get_target_hucs

# Get target HUCs based on configuration
try:
    HUCIDS = get_target_hucs(config)
    print(f"Processing {len(HUCIDS)} HUCs") 
except Exception as e:
    print(f"Error determining HUCs to process: {e}")
    raise

output_base = Path(config['output_base'])

# Common output paths
def get_output_paths(wildcards, prefix=""):
    return {
        'flowlines_raw': f"{output_base}/{prefix}{wildcards.hucid}/{wildcards.hucid}-flowlines_raw.shp",
        'dem': f"{output_base}/{prefix}{wildcards.hucid}/{wildcards.hucid}-dem.tif",
        'flowlines': f"{output_base}/{prefix}{wildcards.hucid}/{wildcards.hucid}-flowlines.shp",
        'floors': f"{output_base}/huc10_all/{wildcards.hucid}-floors.tif",
        'flowlines_out': f"{output_base}/huc10_all/{wildcards.hucid}-flowlines.shp",
        'wp': f"{output_base}/huc10_all/{wildcards.hucid}-wp.shp",
        'log': f"{output_base}/huc10_all/{wildcards.hucid}-run.log",
        'working_dir': f"{output_base}/{prefix}{wildcards.hucid}_working_dir"
    }

## Rules

rule all:
    input:
        expand(output_base / "huc10_all" / "{hucid}-floors.tif", hucid=HUCIDS)

rule prep_all:
    input:
        expand(output_base / "{hucid}/{hucid}-dem.tif", hucid=HUCIDS),
        expand(output_base / "{hucid}/{hucid}-flowlines.shp", hucid=HUCIDS)

rule mosaic:
    input:
        floors_dir = os.path.join(config["output_base"], "huc10_all")
    output:
        mosaic_dir = directory(os.path.join(config["output_base"], "mosaic"))
    shell:
        "poetry run python src/mosaic.py "
        "{input.floors_dir} "
        "{output.mosaic_dir} "
        "--level huc6 "
        "--ocean-clip"  # Default true, explicitly set for clarity

rule mosaic_ca:
    input:
        floors_dir = os.path.join(config["output_base"], "huc10_all")
    output:
        mosaic_dir = directory(os.path.join(config["output_base"], "mosaic_ca"))
    shell:
        "poetry run python src/mosaic.py "
        "{input.floors_dir} "
        "{output.mosaic_dir} "
        "--level huc6 "
        "--ocean-clip "  # Default true, explicitly set for clarity
        "--state-boundary-clip" 

rule download_data:
    params:
        hucid = '{hucid}'
    output:
        dem = output_base / "{hucid}/{hucid}-dem.tif",
        flowlines = output_base / "{hucid}/{hucid}-flowlines_raw.shp"
    resources:
        download_slots=1
    shell:
        "poetry run python src/dl_dem_and_flowlines.py {params.hucid} {output.dem} {output.flowlines}"

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
        output_base / "huc10_all/{hucid}-floors.tif"
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

# Snakefile
from pathlib import Path
import os

# Try to get config-dependent variables, set defaults if no config
try:
    from src.utils import get_target_hucs
    HUCIDS = get_target_hucs(config)
    output_base = Path(config['output_base'])
    params_file = config.get('params_file')
except (NameError, KeyError) as e:
    # Default values when no config is provided
    HUCIDS = []
    output_base = Path("output")
    params_file = "default_params.yaml"
    print("No config file provided - only config-independent rules will work")

# Common output paths
def get_output_paths(wildcards, prefix=""):
    return {
        'flowlines_raw': f"{output_base}/{prefix}{wildcards.hucid}/{wildcards.hucid}-flowlines_raw.shp",
        'dem': f"{output_base}/{prefix}{wildcards.hucid}/{wildcards.hucid}-dem.tif",
        'flowlines': f"{output_base}/{prefix}{wildcards.hucid}/{wildcards.hucid}-flowlines.shp",
        'floors': f"{output_base}/floors/{wildcards.hucid}-floors.tif",
        'flowlines_out': f"{output_base}/floors/{wildcards.hucid}-flowlines.shp",
        'wp': f"{output_base}/floors/{wildcards.hucid}-wp.shp",
        'log': f"{output_base}/floors/{wildcards.hucid}-run.log",
        'working_dir': f"{output_base}/{prefix}{wildcards.hucid}_working_dir"
    }

## Rules that don't require config

rule initialize_whitebox:
    output: 
        touch("whitebox_initialized.flag")
    shell:
        "poetry run python src/init_whitebox.py"

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

## Rules that require config

rule extract_all:
    input:
        expand(output_base / "floors" / "{hucid}-floors.tif", hucid=HUCIDS)
    run:
        if not HUCIDS:
            raise ValueError("No HUCs specified - this rule requires a config file")

rule prep_all:
    input:
        expand(output_base / "{hucid}/{hucid}-dem.tif", hucid=HUCIDS),
        expand(output_base / "{hucid}/{hucid}-flowlines.shp", hucid=HUCIDS)
    run:
        if not HUCIDS:
            raise ValueError("No HUCs specified - this rule requires a config file")

rule mosaic:
    output:
        mosaic_dir = directory(os.path.join(str(output_base), "mosaic"))
    run:
        if not HUCIDS:
            raise ValueError("This rule requires a config file")
        shell(
            "poetry run python src/mosaic.py "
            "{output_base}/floors "
            "{output.mosaic_dir} "
            "--level huc6 "
            "--ocean-clip"
        )

rule mosaic_ca:
    output:
        mosaic_dir = directory(os.path.join(str(output_base), "mosaic_ca"))
    run:
        if not HUCIDS:
            raise ValueError("This rule requires a config file")
        shell(
            "poetry run python src/mosaic.py "
            "{output_base}/floors "
            "{output.mosaic_dir} "
            "--level huc6 "
            "--ocean-clip "
            "--state-boundary-clip"
        )

rule extract_valleys:
    input:
        dem = output_base / "{hucid}/{hucid}-dem.tif",
        network = output_base / "{hucid}/{hucid}-flowlines.shp",
    params:
        param_file = lambda wildcards: params_file,
        working_dir = lambda wildcards: get_output_paths(wildcards)['working_dir'],
        flowlines_ofile = lambda wildcards: get_output_paths(wildcards)['flowlines_out'],
        wp_ofile = lambda wildcards: get_output_paths(wildcards)['wp'],
        log_file = lambda wildcards: get_output_paths(wildcards)['log']
    output:
        output_base / "floors/{hucid}-floors.tif"
    run:
        if not params_file:
            raise ValueError("This rule requires a config file with params_file specified")
        shell(
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
        )

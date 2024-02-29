# CA River Valleys

This repository contains a workflow for generating river valley floor polygons for the state of California.
It uses [pyvalleys](https://github.com/avkoehl/valleys) to extract the valley floor boundaries from 3DEP 10m DEMs and NHD Medium Resolution Flowlines.

# Environment Setup

1. Install Poetry
2. Install Python 3.10+, I recommend using pyenv and setting project-specific python
3. Install the project dependencies `poetry install`
4. Install WhiteBoxTools

Edit the line in the Snakefile within the `rule_extract_valleys` that defines the wbt variable to match the path to the directory on your system
```
rule extract_valleys:
    ...
    params:
        wbt = os.path.expanduser(<WBT_PATH>)
```

# Workflow

The following workflow is applied to each HUCID:

1. Get WBD associated with that HUCID, download and clip 3DEP dem and NHD flowlines to that HUC
2. Mask out non california cells from the DEM by comparing the DEM to the california shapefile
3. Filter the NHD flowlines to only include river segments (e.g no artificial segments)
4. extract valley floors for HUCID

# Run the workflow

Once environment is setup, the workflow can be automated with snakemake.

1. Run on a sample

To run on a sample:

```
poetry run snakemake demo_all --cores 1 
```

2. Run on full state

To run on the all of the HUC8 Watersheds in California. Run the following command:
```
poetry run snakemake all --cores 1
```

3. Run on custom list of watersheds

To run on a custom list of watersheds, edit the line starting with `CUSTOM_HUCIDS =`. 
Then run the command:
```
poetry run snakemake custom_all --cores `
```

# Customizing the Parameters for pyvalleys to use

Pyvalleys can be modified by user defined parameters. These are passed to the module from within a configuration file.

Edit the line in the Snakefile within the `rule_extract_valleys` that defines the path to the configuration file to point to the configuration file you want to use for the run.
```
rule extract_valleys:
    ...
    params:
        config = "configs/base.toml"
```

# Data output paths

Outputs are stored in the following format:

```
# data/
    # {hucid}/
    #     dem_raw.tif
    #     flowlines_raw.tif
    #     dem.tif
    #     flowlines.tif
    #     valley_floors.shp
    #     terrain_attributes/

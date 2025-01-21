# CA Valley Floors

A Python-based workflow for generating high-resolution valley floor polygons
across California using 10m Digital Elevation Models (DEMs) and National
Hydrography Dataset (NHD) flowlines.

## Overview

This project uses [valleyx](https://github.com/avkoehl/valleyx) to extract valley floor boundaries from:
- USGS 3DEP 10-meter Digital Elevation Models
- NHD Medium Resolution Flowlines

The workflow processes data by Hydrologic Unit Code (HUC) regions, allowing for
flexible regional analysis and parallel processing.

## Features

- Automated downloading of DEM and flowline data
- Parallel processing support through Snakemake
- Configurable parameters for valley floor extraction
- Tools for mosaicking and clipping results
- California-specific boundary and ocean clipping

## Prerequisites

- Python 3.10 or higher
- [Poetry](https://python-poetry.org/) for dependency management
- Git for version control

## Installation

1. Clone the repository:
```bash
git clone git@github.com:avkoehl/ca-valley-floors.git
cd ca-valley-floors
```

2. Install dependencies:
```bash
# Basic installation
poetry install

# With development tools (matplotlib, jupyter)
poetry install --with dev
```

## Workflow Steps

The workflow below outlines the steps to generate valley floor polygons for all
the huc10s in California.

### 1. Setup and Configuration

#### Setup 
Run the setup rule to initialize whitebox, download necessary data files such
as the land masks. 
```bash
poetry run snakemake setup -j1
```

To generate the list of all HUCs in California. This is optional if you already
have a list of HUCs you want to process. It will save the list of HUCs to a
file called `data/target_huc10s.csv`.

```bash
poetry run snakemake generate_targets -j1
```

#### Configuration 

Copy the default configuration file:
```bash
cp config.yaml.example my_config.yaml
```

Edit the configuration file to set the hucs_file, params_file, and output_dir for the run:
```yaml
output_dir: "/path/to/output"
hucs_file: "/path/to/hucs.csv"
params_file: "/path/to/params.toml"
```

Alternatively, you can set these variables using the `--config` flag when running snakemake. e.g.:
```bash
poetry run snakemake process --config hucs_file=./data/target_huc10s.csv params_file=params/my_params.toml output_dir=./data/output -j 4
```

### 2. Download DEM and Flowline Data

Download DEMs and flowlines for the target HUCs:
```bash
poetry run snakemake download --resources download_slots=4 --configfile my_config.yaml -j4
```

This download rule is optional and is meant as a convenience to separate the
download step from the processing step. If you run the processing step without
downloading the data, the workflow will automatically download the data as
needed.

### 3. Valley Floor Extraction

Process the target HUCs to extract valley floors:

```bash
poetry run snakemake process --configfile my_config.yaml -j4
```

### 4. Results Processing

Mosaic results and clip to California boundary (includes ocean clipping):
```bash
poetry run snakemake mosaic_ca
```

Mosaic results with ocean clipping only:
```bash
poetry run snakemake mosaic
```

## Customizing Valley Floor Parameters

1. Create a custom parameters file:
```bash
cp params/params_10m.toml params/my_params.toml
```

2. Update the configuration to use your parameters:
```yaml
params_file: 'params/my_params.toml'
```

## Project Structure

```
ca-valley-floors/
├── Snakefile            # Snakemake workflow file
├── params/             
│   └── params_10m.toml  # Valley floor extraction parameters for 10m DEMs
├── data/                # Data directory for files used in the workflow
└── README.md           
```

## Support

For questions or issues, contact:
- Arthur Koehl
- Email: avkoehl at ucdavis.edu

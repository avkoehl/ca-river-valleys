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

## Configuration

### Basic Setup

1. Copy and edit the configuration file:
```bash
cp config.yaml my_config.yaml
```

2. Configure the output directory in `my_config.yaml`:
```yaml
output_base: '/path/to/your/output/directory/'
```

### HUC Selection

The workflow supports three methods for selecting HUC regions (configure only one):

1. Single HUC:
```yaml
huc_id: '18050002'
```

2. Multiple specific HUCs:
```yaml
huc_ids:
  - '1802016306'
  - '1804001211'
```

3. HUC manifest file:
```yaml
huc_manifest: './data/target_huc10s.csv'
prefix: '18'          # Optional: Filter by prefix
sample_size: 5        # Optional: Sample size
random_seed: 14       # Optional: Random seed
```

## Workflow Steps

### 1. Data Preparation
Download DEMs and flowlines:
```bash
poetry run snakemake prep_all --configfile my_config.yaml -j 10 --resources download_slots=10
```

### 2. Valley Floor Extraction
Process the downloaded data:
```bash
poetry run snakemake all --configfile my_config.yaml -j 10
```

### 3. Results Processing

#### Option A: California-specific mosaic
Mosaic results and clip to California boundary (includes ocean clipping):
```bash
poetry run snakemake mosaic_ca
```

#### Option B: General mosaic
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
├── config.yaml          # Main configuration file
├── params/             
│   └── params_10m.toml  # Valley floor extraction parameters
├── data/                # Input data directory
└── README.md           
```

## Support

For questions or issues, contact:
- Arthur Koehl
- Email: avkoehl at ucdavis.edu

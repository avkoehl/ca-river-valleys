import os

import pandas as pd

from pyvalleys.workflow import valley_floors

dem_dir = '../data/3dep_10m_land/'
flow_dir = '../data/nhd_mr/'
output_dir = '../outputs/valley_floors/'
terrain_base = '../outputs/terrain_attributes/'
config_file = './base.toml'
wbt_path = '~/opt/WBT/'

def parse_flowdir(flow_dir):
    files = os.listdir(flow_dir)
    files = [f for f in files if f.endswith('.shp')]
    huc8s = [f.split('-')[0] for f in files]
    full_paths = [os.path.join(flow_dir, f) for f in files]
    df = pd.DataFrame({'huc8': huc8s, 'flow_file': full_paths})
    return df

def parse_demdir(dem_dir):
    files = os.listdir(dem_dir)
    huc8s = [f.split('-')[0] for f in files]
    full_paths = [os.path.join(dem_dir, f) for f in files]
    df = pd.DataFrame({'huc8': huc8s, 'dem_file': full_paths})
    return df

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Get list of DEMs
dem_files = parse_demdir(dem_dir)
flow_files = parse_flowdir(flow_dir)
combined = pd.merge(dem_files, flow_files, on='huc8')

for i, row in combined.iterrows():
    huc8 = row['huc8']
    dem_file = row['dem_file']
    flowlines_file = row['flow_file']

    terrain_dir = os.path.join(terrain_base, huc8)
    ofile = os.path.join(output_dir, huc8 + 'valley_floor.shp')

    print(f'Processing {dem_file} ({i+1}/{len(combined)})')
    valley_floors(dem_file, flowlines_file, config_file, wbt_path, terrain_dir, ofile)



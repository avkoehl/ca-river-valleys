# Description: This file contains the functions to mask the ocean and land from the DEM and the land geometry
import os
import glob

import shapely
from shapely.geometry import mapping
import rioxarray
import geopandas as gpd

def mask_dem(dem, land_geom):
    # Mask the ocean from the DEM
    # clip to geodataframe
    dem = dem.rio.clip(land_geom.geometry.apply(mapping))
    return dem

dem_dir = '../data/3dep_10m/'
output_dir = '../data/3dep_10m_land/'
land_geom = gpd.read_file('../data/california_mask/California.shp')

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for i,dem_file in enumerate(glob.glob(dem_dir + '*.tif')):
    print(dem_file)
    dem = rioxarray.open_rasterio(dem_file, masked=True).squeeze()

    if i == 0:
        land_geom = land_geom.to_crs(dem.rio.crs)

    dem = mask_dem(dem, land_geom)
    dem.rio.to_raster(output_dir + dem_file.split('/')[-1])

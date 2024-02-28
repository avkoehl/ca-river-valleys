# Description: This file contains the functions to mask the ocean and land from the DEM and the land geometry
import os
import glob
import sys

import shapely
from shapely.geometry import mapping
import rioxarray
import geopandas as gpd

from utils import setup_output


def main():
    dem = sys.argv[1]
    land_file = sys.argv[2]
    ofile = sys.argv[3]

    dem = rioxarray.open_rasterio(dem)

    land_geom = gpd.read_file(land_file)
    land_geom = land_geom.to_crs(dem.rio.crs)

    dem = dem.rio.clip(land_geom.geometry.apply(mapping))

    setup_output(ofile)
    dem.rio.to_raster(ofile)

if __name__ == "__main__":
    main()

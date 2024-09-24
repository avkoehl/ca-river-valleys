import os
import sys

from pygeohydro import WBD
from pygeohydro import huc_wb_full
from pynhd import NHD
import py3dep

from utils import setup_output


def get_dem_and_flowlines(hucid, layer):
    wbd = WBD(layer)
    boundary = wbd.byids(layer, hucid)
    boundary_reprojected = boundary.to_crs(3310)

    dem = py3dep.static_3dep_dem(boundary.geometry.iloc[0], resolution=10, crs=4326)
    dem = dem.rio.reproject(3310)

    nhd_mr = NHD("flowline_mr")
    flowlines_mr = nhd_mr.bygeom(boundary.geometry.iloc[0].bounds)
    flowlines_mr = flowlines_mr.to_crs(3310)
    flowlines_mr = flowlines_mr.clip(boundary_reprojected.geometry.iloc[0])

    return dem, flowlines_mr

def main():
    hucid = sys.argv[1]
    dem_path = sys.argv[2]
    nhd_path =  sys.argv[3]

    layer = 'huc' + str(len(hucid))

    dem, flowlines = get_dem_and_flowlines(hucid, layer)

    [setup_output(fname) for fname in [dem_path, nhd_path]]

    dem.rio.to_raster(dem_path)
    flowlines.to_file(nhd_path)

if __name__ == "__main__":
    main()

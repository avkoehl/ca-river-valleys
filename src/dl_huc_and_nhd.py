import os

from pygeohydro import WBD
from pygeohydro import huc_wb_full
from pynhd import NHD
import py3dep

def get_dem_and_flowlines(hucid, layer):
    wbd = WBD(layer)
    boundary = wbd.byids(layer, hucid)
    boundary_reprojected = boundary.to_crs(3310)

    dem = py3dep.get_map("DEM", boundary.geometry.iloc[0], resolution=10, geo_crs=boundary.crs, crs=4326)
    dem = dem.rio.reproject(3310)

    nhd_mr = NHD("flowline_mr")
    flowlines_mr = nhd_mr.bygeom(boundary.geometry.iloc[0].bounds)
    flowlines_mr = flowlines_mr.to_crs(3310)
    flowlines_mr = flowlines_mr.clip(boundary_reprojected.geometry.iloc[0])

    return dem, flowlines_mr

def get_huc(hucid, layer, dem_ofile, flowlines_ofile):
    dem, flowlines_mr = get_dem_and_flowlines(hucid, layer)
    dem.rio.to_raster(dem_ofile)
    flowlines_mr.to_file(flowlines_ofile)

huc8_all = huc_wb_full(8)
huc8_all = huc8_all.loc[huc8_all['huc2'] == '18'] # filter to california

#for huc8 in huc8_all['huc8']:
#    print(huc8)
#    get_huc(huc8, 'huc8', odir='../data/')

dem_dir = '../data/3dep_10m/'
flowlines_dir = '../data/nhd_mr/'

if not os.path.exists(dem_dir):
    os.makedirs(dem_dir)
if not os.path.exists(flowlines_dir):
    os.makedirs(flowlines_dir)

huc8 = huc8_all.iloc[0]['huc8']
get_huc(huc8, 'huc8', os.path.join(dem_dir, f'{huc8}-10mdem.tif'), os.path.join(flowlines_dir, f'{huc8}-mrflowlines.shp'))

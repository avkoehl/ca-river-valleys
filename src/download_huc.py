import os
import sys

import rasterio
from pygeohydro import WBD
from pygeohydro import huc_wb_full
from pynhd import NHD
import py3dep

from utils import setup_output


def get_dem_and_flowlines(hucid, layer):
    wbd = WBD(layer)
    boundary = wbd.byids(layer, hucid)
    boundary_reprojected = boundary.to_crs(3310)

    try:
        dem = py3dep.static_3dep_dem(boundary.geometry.iloc[0], resolution=10, crs=4326)
    except:
        dem = retry_on_smaller(boundary)

    dem = dem.rio.reproject("EPSG:3310", 
            resampling=rasterio.enums.Resampling.bilinear)
    nhd_mr = NHD("flowline_mr")
    flowlines_mr = nhd_mr.bygeom(boundary.geometry.iloc[0].bounds)
    flowlines_mr = flowlines_mr.to_crs(3310)
    flowlines_mr = flowlines_mr.clip(boundary_reprojected.geometry.iloc[0])

    return dem, flowlines_mr

def retry_on_smaller(boundary):
    bbox = boundary.bounds
    bbox['mid_x'] = (bbox['minx'] + bbox['maxx']) / 2
    bbox['mid_y'] = (bbox['miny'] + bbox['maxy']) / 2
    
    # Create four smaller bounding boxes
    split_bboxes = pd.DataFrame([
        {'minx': bbox.iloc[0]['minx'], 'miny': bbox.iloc[0]['miny'], 'maxx': bbox.iloc[0]['mid_x'], 'maxy': bbox.iloc[0]['mid_y']},  # Bottom-left
        {'minx': bbox.iloc[0]['mid_x'], 'miny': bbox.iloc[0]['miny'], 'maxx': bbox.iloc[0]['maxx'], 'maxy': bbox.iloc[0]['mid_y']},  # Bottom-right
        {'minx': bbox.iloc[0]['minx'], 'miny': bbox.iloc[0]['mid_y'], 'maxx': bbox.iloc[0]['mid_x'], 'maxy': bbox.iloc[0]['maxy']},  # Top-left
        {'minx': bbox.iloc[0]['mid_x'], 'miny': bbox.iloc[0]['mid_y'], 'maxx': bbox.iloc[0]['maxx'], 'maxy': bbox.iloc[0]['maxy']}   # Top-right
    ])
    
    dems = []
    for ind,box in split_bboxes.iterrows():
        dems.append(py3dep.get_dem(tuple(box), crs="EPSG:4326", resolution=10))

    mosaic = merge_arrays(dems)
    clipped = mosaic.rio.clip(boundary)
    return clipped

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

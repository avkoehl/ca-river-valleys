"""
Download NHD flowlines and DEM for a given HUCID.
"""

import argparse
import os

import geopandas as gpd
import pandas as pd
import py3dep
from rioxarray.merge import merge_arrays
from pynhd import NHD
import rasterio
from pygeohydro import WBD
from shapely.geometry import box
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon


def clip_out_ocean(boundary, land_df):
    land_df = land_df.to_crs(boundary.crs)
    boundary = boundary.clip(land_df)
    return boundary


def get_boundary(hucid, layer="huc10"):
    wbd = WBD(layer)
    boundary = wbd.byids(layer, hucid)
    return boundary["geometry"], boundary["states"]


def get_nhd(boundary):
    nhd = NHD("flowline_mr")
    if isinstance(boundary, MultiPolygon):
        bbox = box(*boundary.bounds)
        flow = nhd.bygeom(bbox)
        flow = flow.clip(boundary)
    else:  # Polygon
        flow = nhd.bygeom(boundary)

    flow = flow[flow.geometry.type == "LineString"]
    flow = flow.to_crs("EPSG:3310")
    return flow


def get_dem(boundary):
    try:
        dem = py3dep.static_3dep_dem(boundary, resolution=10, crs=4326)
    except:
        dem = retry_on_smaller(boundary)

    dem = dem.rio.reproject("EPSG:3310", resampling=rasterio.enums.Resampling.bilinear)
    return dem


def retry_on_smaller(boundary):
    bbox = pd.DataFrame(
        {
            "minx": [boundary.bounds[0]],
            "miny": [boundary.bounds[1]],
            "maxx": [boundary.bounds[2]],
            "maxy": [boundary.bounds[3]],
        }
    )
    bbox["mid_x"] = (bbox["minx"] + bbox["maxx"]) / 2
    bbox["mid_y"] = (bbox["miny"] + bbox["maxy"]) / 2

    # Create four smaller bounding boxes
    split_bboxes = pd.DataFrame(
        [
            {
                "minx": bbox.iloc[0]["minx"],
                "miny": bbox.iloc[0]["miny"],
                "maxx": bbox.iloc[0]["mid_x"],
                "maxy": bbox.iloc[0]["mid_y"],
            },  # Bottom-left
            {
                "minx": bbox.iloc[0]["mid_x"],
                "miny": bbox.iloc[0]["miny"],
                "maxx": bbox.iloc[0]["maxx"],
                "maxy": bbox.iloc[0]["mid_y"],
            },  # Bottom-right
            {
                "minx": bbox.iloc[0]["minx"],
                "miny": bbox.iloc[0]["mid_y"],
                "maxx": bbox.iloc[0]["mid_x"],
                "maxy": bbox.iloc[0]["maxy"],
            },  # Top-left
            {
                "minx": bbox.iloc[0]["mid_x"],
                "miny": bbox.iloc[0]["mid_y"],
                "maxx": bbox.iloc[0]["maxx"],
                "maxy": bbox.iloc[0]["maxy"],
            },  # Top-right
        ]
    )

    dems = []
    for _, box in split_bboxes.iterrows():
        dems.append(py3dep.get_dem(tuple(box), crs="EPSG:4326", resolution=10))

    mosaic = merge_arrays(dems)
    clipped = mosaic.rio.clip(boundary)
    return clipped


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("hucid", type=str)
    parser.add_argument("dem_ofile", type=str)
    parser.add_argument("flowline_ofile", type=str)
    parser.add_argument("us_land_file", type=str)
    parser.add_argument("na_land_file", type=str)
    args = parser.parse_args()

    # get odirs from ofiles and create directories if they don't exist
    dem_odir = os.path.dirname(args.dem_ofile)
    flowline_odir = os.path.dirname(args.flowline_ofile)
    if not os.path.exists(dem_odir):
        os.makedirs(dem_odir)
    if not os.path.exists(flowline_odir):
        os.makedirs(flowline_odir)

    boundary, states = get_boundary(args.hucid)

    # clip out ocean
    # if MX in states us na_land_file, else us_land_file
    # handle this smarter states is a series of strings
    mx_flag = False
    for element in states:
        if "MX" in element:
            mx_flag = True

    if mx_flag:
        land_df = gpd.read_file(args.na_land_file)
    else:
        land_df = gpd.read_file(args.us_land_file)
    boundary = clip_out_ocean(boundary, land_df)

    # if boundary is geoseries, convert to shapely geometry
    if isinstance(boundary, gpd.GeoSeries):
        boundary = boundary.union_all()

    if boundary is None:
        raise ValueError("Boundary is empty")

    if not isinstance(boundary, (Polygon, MultiPolygon)):
        raise ValueError("Boundary is not a polygon, or multipolygon")

    failed_nhd = False
    failed_dem = False
    try:
        nhd = get_nhd(boundary)
        nhd.to_file(args.flowline_ofile)
    except Exception as e:
        failed_nhd = True
        print(f"Failed to download NHD: {e}")
        nhd = None

    try:
        dem = get_dem(boundary)
        dem.rio.to_raster(args.dem_ofile)
    except Exception as e:
        failed_dem = True
        print(f"Failed to download DEM: {e}")
        dem = None

    if failed_nhd or failed_dem:
        raise ValueError(
            f"Failed to download data: NHD_failed={failed_nhd}, DEM_failed={failed_dem}"
        )

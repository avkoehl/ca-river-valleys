import os

import pandas as pd
import py3dep
from rioxarray.merge import merge_arrays
from pynhd import NHD
import rasterio
from pygeohydro import WBD
from shapely.geometry import box


def get_boundary(hucid, layer="huc10"):
    wbd = WBD(layer)
    boundary = wbd.byids(layer, hucid)
    return boundary["geometry"]


def get_nhd(boundary):
    nhd = NHD("flowline_mr")
    flow = nhd.bygeom(boundary.total_bounds)
    flow = flow.clip(boundary)
    flow = flow[flow.geometry.type == "LineString"]
    return flow


def get_dem(boundary):
    try:
        dem = py3dep.static_3dep_dem(
            box(*boundary.total_bounds), resolution=10, crs=4326
        )
    except:
        dem = retry_on_smaller(boundary)

    dem = dem.rio.clip(boundary)
    dem = dem.rio.reproject("EPSG:3310", resampling=rasterio.enums.Resampling.bilinear)
    return dem


def retry_on_smaller(boundary):
    bbox = pd.DataFrame(
        {
            "minx": [boundary.total_bounds[0]],
            "miny": [boundary.total_bounds[1]],
            "maxx": [boundary.total_bounds[2]],
            "maxy": [boundary.total_bounds[3]],
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


special_cases = pd.read_csv("../data/special_cases.csv")
odir_base = "../../20250114/"

failures = []


for idx, row in special_cases.iterrows():
    hucid = row["huc"]
    name = row["name"]
    print(f"Processing {hucid}")

    try:
        boundary = get_boundary(hucid)
        odir = f"{odir_base}/{hucid}"
        os.makedirs(odir, exist_ok=True)
    except Exception as e:
        failures.append(
            {"huc": hucid, "name": name, "reason": "failed on get_boundary"}
        )
        continue

    try:
        nhd = get_nhd(boundary)
        nhd.to_file(f"{odir}/{hucid}-flowlines.shp")
    except Exception as e:
        failures.append({"huc": hucid, "name": name, "reason": "failed on get_nhd"})

    try:
        dem = get_dem(boundary)
        dem.rio.to_raster(f"{odir}/{hucid}-dem.tif")
    except Exception as e:
        failures.append({"huc": hucid, "name": name, "reason": "failed on get_dem"})

# Save failure log
if failures:
    pd.DataFrame(failures).to_csv("failed_hucs.csv", index=False)
    print("\nFailed HUCs:")
    for f in failures:
        print(f"{f['huc']} ({f['name']}): {f['reason']}")

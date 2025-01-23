"""
mosaic, binarize
clip out ocean
optional clip to california state boundary

args:
input_dir
output_dir
level = huc06 (or none, or huc2, huc4, huc6, huc8)
state_boundary_clip = False
"""

import argparse
import os
from glob import glob

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.merge import merge
import rioxarray as rxr


def setup_parser():
    parser = argparse.ArgumentParser(
        description="Mosaic results to HUC level and clipping parameters"
    )
    # Required arguments
    parser.add_argument("input_dir", help="Input directory path")
    parser.add_argument("output_dir", help="Output directory path")
    parser.add_argument("na_land_file", help="Path to North America land shape file")
    parser.add_argument("us_land_file", help="Path to USA land shape file")

    # Optional arguments
    parser.add_argument(
        "--level",
        choices=["huc2", "huc4", "huc6", "huc8", None],
        default="huc6",
        help="HUC level to process (huc2, huc4, huc6, huc8, or None)",
    )

    parser.add_argument(
        "--state-boundary-clip",
        action="store_true",
        default=False,
        help="Enable state boundary clipping (default: False)",
    )

    return parser


def mosaic(tif_files):
    src_files = [rasterio.open(f) for f in tif_files]
    mosaic, out_t = merge(src_files)

    binary = np.where(mosaic[0] > 0, 1, 0)
    for src in src_files:
        src.close()
        with rasterio.open(tif_files.iloc[0]) as src:
            out_meta = src.meta.copy()
        out_meta.update(
            {"height": binary.shape[0], "width": binary.shape[1], "transform": out_t}
        )

    with rasterio.open("temp_binary.tif", "w", **out_meta) as dst:
        dst.write(binary.astype(rasterio.float32), 1)

    binary = rxr.open_rasterio("temp_binary.tif", masked=True)
    binary = binary.squeeze()
    binary = binary.fillna(255)
    binary = binary.rio.write_nodata(255)
    binary = binary.astype(np.uint8)

    os.remove("temp_binary.tif")
    return binary


def load_floor_files(input_dir, level):
    floor_files = glob(f"{input_dir}/*.tif")
    records = []
    for file in floor_files:
        huc10 = file.split("/")[-1].split("-")[0]

        if level is None:
            group = "all"
        else:
            digits = int(level[-1])
            group = huc10[0:digits]
        records.append({"huc10": huc10, "filename": file, "group": group})
    df = pd.DataFrame.from_records(records)
    return df


def land_mask(na, usa):
    # land =
    # california + nevada + arizona + oregon + mexico (from us)
    # + mexico (from na) + buffer 1
    # union_all
    # this is because accuracy for north america is less than for usa
    # but need to inlcude Mexico
    # buffer is to handle the little gap between the two
    states = usa.loc[usa["STATE"].isin(["CA", "NV", "AZ", "OR"]), "geometry"]
    mexico = na.loc[na["NAME"] == "Mexico", "geometry"]
    states = states.to_crs("EPSG:3310")
    mexico = mexico.to_crs("EPSG:3310")
    mexico = mexico.buffer(1000)

    land = gpd.GeoDataFrame(geometry=pd.concat([states, mexico], ignore_index=True))
    land = gpd.GeoSeries(land.union_all())
    land.crs = "EPSG:3310"
    return land


if __name__ == "__main__":
    parser = setup_parser()
    args = parser.parse_args()

    usa = gpd.read_file(args.us_land_file)
    na = gpd.read_file(args.na_land_file)

    os.makedirs(args.output_dir, exist_ok=True)

    floors = load_floor_files(args.input_dir, args.level)
    for group in floors["group"].unique():
        tif_files = floors.loc[floors["group"] == group, "filename"]
        binary_mosaic = mosaic(tif_files)

        if args.state_boundary_clip:
            ca = usa.loc[usa["STATE"] == "CA", "geometry"]
            ca = ca.to_crs(binary_mosaic.rio.crs)
            binary_mosaic = binary_mosaic.rio.clip(ca)
        else:
            mask = land_mask(na, usa)
            binary_mosaic = binary_mosaic.rio.clip(mask.geometry)

        binary_mosaic.rio.to_raster(f"{args.output_dir}/{group}-floors.tif")

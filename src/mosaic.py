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

    # Optional arguments
    parser.add_argument(
        "--level",
        choices=["huc2", "huc4", "huc6", "huc8", None],
        default="huc6",
        help="HUC level to process (huc2, huc4, huc6, huc8, or None)",
    )
    parser.add_argument(
        "--no-ocean-clip",
        action="store_false",
        dest="ocean_clip",
        help="Disable ocean clipping",
    )
    parser.add_argument(
        "--state-boundary-clip",
        action="store_true",
        default=False,
        help="Enable state boundary clipping (default: False)",
    )

    return parser


def clip_to_geometries(raster, boundaries):
    mask = raster.rio.clip(boundaries.geometry, all_touched=True, drop=False)
    masked_raster = raster.copy()
    masked_raster = masked_raster.where(~np.isnan(mask))
    return masked_raster


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


if __name__ == "__main__":
    parser = setup_parser()
    args = parser.parse_args()

    if args.state_boundary_clip:
        us_geoms = gpd.read_file("./data/s_05mr24/s_05mr24.shp")
        ca_state_geoms = us_geoms.loc[us_geoms["STATE"] == "CA"]
        ca_state_geoms = ca_state_geoms.to_crs("EPSG:3310")

    os.makedirs(args.output_dir, exist_ok=True)

    floors = load_floor_files(args.input_dir, args.level)
    for group in floors["group"].unique():
        tif_files = floors.loc[floors["group"] == group, "filename"]
        binary_mosaic = mosaic(tif_files)

        if args.state_boundary_clip:
            binary_mosaic = clip_to_geometries(binary_mosaic, ca_state_geoms)

        binary_mosaic.rio.to_raster(f"{args.output_dir}/{group}-floors.tif")

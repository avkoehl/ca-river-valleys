"""
mosaic, binarize
clip out ocean
optional clip to california state boundary

args:
input_dir
output_dir
level = huc6 (or none, or huc2, huc4, huc6, huc8)
state_boundary_clip = False
"""

import argparse
import os
from glob import glob

import xarray as xr
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import rioxarray as rxr
from rasterio.merge import merge
from shapely.geometry import shape
import rasterio.features


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
        type=str,
        choices=["huc2", "huc4", "huc6", "huc8"],
        default=None,
        help="HUC level to process (huc2, huc4, huc6, huc8)",
    )

    parser.add_argument(
        "--state-boundary-clip",
        action="store_true",
        default=False,
        help="Enable state boundary clipping (default: False)",
    )
    parser.add_argument(
        "--watershed-boundary-clip",
        action="store_true",
        default=False,
        help="Enable watershed boundary clipping (default: False)",
    )

    return parser


def mosaic(tif_files):
    src_files = [rasterio.open(f) for f in tif_files]
    mosaic, out_transform = merge(src_files)

    src_crs = src_files[0].crs
    for src in src_files:
        src.close()

    mosaic = mosaic.squeeze()
    mosaic = mosaic.astype(np.uint8)
    mosaic[mosaic > 0] = 1

    da = xr.DataArray(
        mosaic,
        dims=["y", "x"],
        coords={
            "y": np.arange(mosaic.shape[0]) * out_transform.e + out_transform.f,
            "x": np.arange(mosaic.shape[1]) * out_transform.a + out_transform.c,
        },
    )

    da = da.rio.write_transform(out_transform)
    da = da.rio.write_crs(src_crs)
    da = da.rio.write_nodata(255)
    return da


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

    if args.watershed_boundary_clip:
        floors = floors[floors["huc10"].str.startswith("18")]

    for group in floors["group"].unique():
        tif_files = floors.loc[floors["group"] == group, "filename"]

        binary_mosaic = mosaic(tif_files)

        if args.state_boundary_clip:
            ca = usa.loc[usa["STATE"] == "CA", "geometry"]
            ca = ca.to_crs(binary_mosaic.rio.crs)
            binary_mosaic = binary_mosaic.rio.clip(ca, drop=True, from_disk=True)
        else:
            mask = land_mask(na, usa)
            mask = mask.to_crs(binary_mosaic.rio.crs)
            binary_mosaic = binary_mosaic.rio.clip(
                mask.geometry, drop=True, from_disk=True
            )

        binary_mosaic.rio.to_raster(
            f"{args.output_dir}/{group}-floors.tif",
            driver="COG",
            dtype="uint8",
            compress="lzw",
            nodata=255,
        )
        print(f"Saved {args.output_dir}/{group}-floors.tif")
        shapes = rasterio.features.shapes(
            binary_mosaic.values, transform=binary_mosaic.rio.transform()
        )
        geoms = [shape(s) for s, v in shapes if v == 1]
        geoms = gpd.GeoDataFrame(geometry=geoms, crs=binary_mosaic.rio.crs)
        geoms.to_file(f"{args.output_dir}/{group}-floors.gpkg", driver="GPKG")
        print(f"Saved {args.output_dir}/{group}-floors.gpkg")

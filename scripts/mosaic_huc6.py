# load in all the tif filenames
# for each huc 6, load all the files and moasaic and clip to california land
# polygon
# save

from glob import glob

import geopandas as gpd
from shapely.geometry import MultiPolygon
from shapely.geometry import Polygon
from rasterio.merge import merge
import rioxarray as rxr
import rasterio
import numpy as np
import pandas as pd
from pygeohydro.watershed import huc_wb_full


# 1. GET HUC BOUNDARIES AND CLIP OUT OCEAN
huc6 = huc_wb_full(6)
ca_huc6 = huc6.loc[huc6["huc2"] == "18"]
ca_huc6 = ca_huc6.to_crs("EPSG:3310")
land = gpd.read_file("../data/california_mask/California.shp")

# clip to land
coastal_huc6_list = ["180101", "180500", "180600", "180701", "180702", "180703"]
boundaries = []
for _, row in ca_huc6.iterrows():
    hucid = row["huc6"]
    geom = row["geometry"]

    if hucid in coastal_huc6_list:
        geom_clipped = geom.intersection(land["geometry"])
        for poly in geom_clipped:
            if not poly.is_empty:
                boundaries.append({"hucid": hucid, "geometry": poly})

    else:
        if isinstance(geom, Polygon):
            boundaries.append({"hucid": hucid, "geometry": geom})

        if isinstance(geom, MultiPolygon):
            for poly in geom.geoms:
                boundaries.append({"hucid": hucid, "geometry": poly})

huc6_boundaries = gpd.GeoDataFrame.from_records(boundaries)
huc6_boundaries = huc6_boundaries.set_geometry("geometry")
huc6_boundaries = huc6_boundaries.set_crs("EPSG:3310")
huc6_boundaries = huc6_boundaries.explode()


# 2. LOAD MANIFEST OF ALL FLOORS.tif FILES
# load in all the tif filenames
floors = glob("../../20241231-CA_floors/*.tif")
records = []
for file in floors:
    huc10 = file.split("/")[-1].split("-")[0]
    huc6 = huc10[0:6]
    records.append({"huc10": huc10, "huc6": huc6, "filename": file})


manifest = pd.DataFrame.from_records(records)

# 3. FOREACH HUC6 MOSAIC THE FLOORS
for hucid in manifest["huc6"].unique():
    tif_files = manifest["filename"].loc[manifest["huc6"] == hucid]
    src_files = [rasterio.open(f) for f in tif_files]
    mosaic, out_transform = merge(src_files)

    # Create binary array where values > 0
    binary = np.where(mosaic[0] > 0, 1, 0)

    # Close source files
    for src in src_files:
        src.close()

    # Get metadata from first file for output
    with rasterio.open(tif_files.iloc[0]) as src:
        out_meta = src.meta.copy()

    # Update metadata for the merged raster
    out_meta.update(
        {
            "height": binary.shape[0],
            "width": binary.shape[1],
            "transform": out_transform,
        }
    )

    # Save binary raster temporarily
    with rasterio.open("temp_binary.tif", "w", **out_meta) as dest:
        dest.write(binary.astype(rasterio.float32), 1)

    binary = rxr.open_rasterio("temp_binary.tif", masked=True)

    # clip
    boundaries = huc6_boundaries.loc[huc6_boundaries["hucid"] == hucid]
    mask = binary.rio.clip(boundaries.geometry, all_touched=True, drop=False)
    masked_raster = binary.copy()
    masked_raster = masked_raster.where(~np.isnan(mask))

    # set nodata
    masked_raster = masked_raster.fillna(255)
    masked_raster = masked_raster.rio.write_nodata(255)
    masked_raster = masked_raster.astype(np.uint8)
    masked_raster.rio.to_raster(f"{hucid}-floors.tif")

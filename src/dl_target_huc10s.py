"""
Generate a list of all the target huc 10s, the union of:
1) all huc10s that are within the HUC02 - '18' - "California Region" boundary
2) all huc10s that intersect with the boundary of the state of Calfornia

save as target_huc10s.csv
"""

import geopandas as gpd
from shapely.geometry import box
import pandas as pd
from pygeohydro.watershed import WBD
from pygeohydro.watershed import huc_wb_full


def dl_california_region_wbd():
    huc2_boundaries = huc_wb_full(2)
    huc2_boundaries = huc2_boundaries.loc[:, ~huc2_boundaries.columns.duplicated()]
    huc_18 = huc2_boundaries.loc[huc2_boundaries["huc2"] == "18", "geometry"]
    exploded = huc_18.explode()
    df = gpd.GeoDataFrame(exploded)
    return df


def load_ca_state_boundary():
    state_boundary = gpd.read_file("../data/california_mask/California.shp")
    return state_boundary


def huc10s_contained(boundaries):
    boundaries = boundaries.to_crs("EPSG:4326")
    wbd_level = WBD("huc10")
    bbox = box(*boundaries.total_bounds)
    huc10s = wbd_level.bygeom(bbox, geo_crs=boundaries.crs)
    intersecting = gpd.sjoin(huc10s, boundaries, predicate="intersects")
    intersecting["level"] = "huc10"
    intersecting["hucid"] = intersecting["huc10"]
    df = intersecting[["hucid", "level"]]
    return df.drop_duplicates()


if __name__ == "__main__":
    print("getting California Region watershed boundary")
    ca_watershed_boundaries = dl_california_region_wbd()
    print("getting California State boundary")
    ca_state_boundaries = load_ca_state_boundary()

    print("getting list of all huc10s Region boundaries")
    watershed_hucs_list = huc10s_contained(ca_watershed_boundaries)
    print("getting list of all huc10s within State boundaries")
    state_hucs_list = huc10s_contained(ca_state_boundaries)
    combined = pd.concat([watershed_hucs_list, state_hucs_list])
    combined = combined.drop_duplicates()
    print("saving to file")
    combined.to_csv("../data/target_huc10s.csv")

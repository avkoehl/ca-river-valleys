"""
Generate a list of all the target huc 10s, the union of:
1) all huc10s that are within the HUC02 - '18' - "California Region" boundary
2) all huc10s that intersect with the boundary of the state of Calfornia

save as target_huc10s.csv
"""

import geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union
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
    state_boundary = gpd.read_file("../data/s_05mr24/s_05mr24.shp")
    state_boundary = state_boundary.loc[state_boundary["STATE"] == "CA", "geometry"]
    df = gpd.GeoDataFrame(state_boundary.explode())
    return df


def huc10s_contained(boundaries, min_intersection_pct=0):
    boundaries = boundaries.to_crs("EPSG:4326")
    wbd_level = WBD("huc10")
    bbox = box(*boundaries.total_bounds)
    huc10s = wbd_level.bygeom(bbox, geo_crs=boundaries.crs)
    intersecting = gpd.sjoin(huc10s, boundaries, predicate="intersects")

    if min_intersection_pct > 0:
        # Calculate intersection area percentage for each HUC10
        # Convert to equal area projection for accurate area calculation
        equal_area_crs = "EPSG:3310"
        boundaries_proj = boundaries.to_crs(equal_area_crs)
        boundaries_proj = unary_union(boundaries_proj.geometry)
        intersecting_proj = intersecting.to_crs(equal_area_crs)

        # Calculate areas
        def calc_intersection_pct(row):
            huc_geom = row.geometry
            intersection = huc_geom.intersection(boundaries_proj)
            return (intersection.area / huc_geom.area) * 100

        intersecting["intersection_pct"] = intersecting_proj.apply(
            calc_intersection_pct, axis=1
        )

        # Filter by minimum intersection percentage
        intersecting = intersecting[
            intersecting.intersection_pct >= min_intersection_pct
        ]

    intersecting["level"] = "huc10"
    intersecting["hucid"] = intersecting["huc10"]
    return intersecting


if __name__ == "__main__":
    print("getting California Region watershed boundary")
    ca_watershed_boundaries = dl_california_region_wbd()
    print("getting California State boundary")
    ca_state_boundaries = load_ca_state_boundary()

    print("getting list of all huc10s Region boundaries")
    watershed_hucs_list = huc10s_contained(
        ca_watershed_boundaries, min_intersection_pct=1
    )
    print("getting list of all huc10s within State boundaries")
    state_hucs_list = huc10s_contained(ca_state_boundaries)
    combined = pd.concat(
        [watershed_hucs_list[["hucid", "level"]], state_hucs_list[["hucid", "level"]]]
    )
    combined = combined.drop_duplicates()

    print("saving to file")
    combined.to_csv("../data/target_huc10s.csv")

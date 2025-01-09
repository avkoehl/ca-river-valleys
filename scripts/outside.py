"""

Get a list of all the huc10s that are within huc2 == 18
but are outside the bounds of California
so that I can rerun them

"""

import os

import geopandas as gpd

manifest = gpd.read_file("../data/huc_manifest/huc_manifest.shp")
manifest = manifest.to_crs("EPSG:3310")
california = gpd.read_file("../data/california_mask/California.shp")

huc10s = manifest.loc[manifest["level"] == "huc10"]

ca_boundary = california.unary_union
outside_hucs = huc10s[~huc10s.within(ca_boundary)]
unique = outside_hucs["hucid"].unique()

for hucid in unique:
    files = {
        "floor_file": f"/dsl/valleys/cleanup/floors/{hucid}-floors.shp",
        "flow_file": f"/dsl/valleys/cleanup/floors/{hucid}-flowlines.shp",
        "wp_file": f"/dsl/valleys/cleanup/floors/{hucid}-wp.shp",
        "log_file": f"/dsl/valleys/cleanup/floors/{hucid}-run.log",
    }

    for key, fname in files.items():
        if os.path.exists(fname):
            os.remove(fname)

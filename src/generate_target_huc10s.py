"""
Generate a list of all the target huc 10s, the union of:
1) all huc10s that are within the HUC02 - '18' - "California Region" boundary
2) all huc10s that intersect with the boundary of the state of Calfornia
3) remove huc10s in the ignore list (e.g. huc10s that are not in the NHD medium resolution dataset)

save names in data/target_huc10s.csv (hucid, states)
"""

import pandas as pd
from pygeohydro.watershed import huc_wb_full

# these huc10s are ignored because they are not in the NHD medium resolution
# dataset some simply do not have any flowlines (e.g. Farallon Islands
# 1805000506) and others are entirely outside the US (e.g 1807030506 in Mexico)
IGNORE_LIST = [
    "1805000506",  # farallon islands no flowlines
    "1807030501",
    "1807030502",
    "1807030503",
    "1807030504",
    "1807030506",
    "1807030507",
    "1710031206",  # oregon coast no flowlines
]

if __name__ == "__main__":
    print("getting list of all huc10s")
    huc10_boundaries = huc_wb_full(10)

    print("getting list of all huc10s within Region 18 watershed boundaries")
    watershed_huc10s = huc10_boundaries.loc[huc10_boundaries["huc2"] == "18"]

    print("getting list of all huc10s within State boundaries")
    # fill None in the state column to avoid errors
    huc10_boundaries["states"] = huc10_boundaries["states"].fillna("None")
    state_huc10s = huc10_boundaries.loc[huc10_boundaries["states"].str.contains("CA")]

    # combined
    print("combining lists")
    combined = pd.concat([watershed_huc10s, state_huc10s])
    combined = combined.drop_duplicates(subset=["huc10"])

    combined = combined.rename(columns={"huc10": "hucid"})

    # remove huc10s in the ignore lists
    combined = combined[~combined["hucid"].isin(IGNORE_LIST)]

    print("saving to files")
    combined_list = combined[["hucid", "states"]]
    combined_list.to_csv("./data/target_huc10s.csv")

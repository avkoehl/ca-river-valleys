import os 

import numpy as np
import pandas as pd
import geopandas as gpd
from pygeohydro.watershed import huc_wb_full
from pygeohydro.watershed import WBD
"""
download a list of all hucs and their level
filter to CA
geometry, hucid, level
to be used to download the dem, and the flowlines by geom later
"""

def download_huc_manifest(levels):
    # WBD can cause issues running with ipython and jupyter, run in regular python shell
    # get California HUC 2 Geometry
    huc2_boundaries = huc_wb_full(2)
    huc2_boundaries = huc2_boundaries.loc[:, ~huc2_boundaries.columns.duplicated()]
    ca_huc2_boundary = huc2_boundaries.loc[huc2_boundaries['huc2'] == '18', "geometry"]
    # CA HUC boundary has a bunch of islands, keep only the mainland for query
    exploded = ca_huc2_boundary.explode()
    main_boundary = exploded.iloc[np.argmax(exploded.area)]

    records = []
    for level in levels:
        print(f"get boundaries for level: {level}")
        huc_level = 'huc' + str(level)
        wbd_level = WBD(huc_level)
        boundaries = wbd_level.bygeom(main_boundary, geo_crs =
                                      huc2_boundaries.crs)

        boundaries = boundaries.explode() # again with the islands
        print(f"found {len(boundaries)} polygons")

        for index, row in boundaries.iterrows():
            record = {
                    'geometry': row['geometry'],
                    'hucid': row[huc_level],
                    'level': huc_level
                    }
            records.append(record)


    df = pd.DataFrame.from_records(records)
    gdf = gpd.GeoDataFrame(df, crs=huc2_boundaries.crs, geometry='geometry')
    df = df[['hucid', 'level']]
    df = df.drop_duplicates() # since boundaries are exploded they may be duplicated
    return df, gdf




if __name__ == "__main__":
    shapefile = "../data/huc_manifest/huc_manifest.shp"
    csvfile = "../data/huc_manifest/huc_manifest.csv"

    if not os.path.exists(os.path.dirname(shapefile)):
        os.makedirs(os.path.dirname(shapefile))
    if not os.path.exists(os.path.dirname(csvfile)):
        os.makedirs(os.path.dirname(csvfile))
    
    levels = [6,8,10,12]
    df, gdf = download_huc_manifest(levels)
    df.to_csv(csvfile)
    gdf.to_file(shapefile)

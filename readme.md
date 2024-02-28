```
# data/
    # {hucid}/
    #     dem_raw.tif
    #     flowlines_raw.tif
    #     dem.tif
    #     flowlines.tif
    #     valley_floors.shp
    #     terrain_attributes/

# workflow:
#       download dem, flowline (hucid)
#       preprocess dem (dem)
#       preprocess flowline (flowline)
#       extract valleys (preprocessed_dem, preprocessed_flowline, config)
```

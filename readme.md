use pyvalleys package

folder of data
    usgs_10m/
        <huc8>_dem.tif
    nhd_mr/
        <huc8>_flowlines-mr.shp

folder of outputs:
    terrain_attributes/
        <huc8>/
            slope.tif,
            curvature.tif,
            …
    valley_floors-<date>/
        params.toml
        <huc8>_valley_floors.shp


01_dl_huc8.py
02_extract_valley_floors.py

load config
iterate through huc8_dem, huc8_flowline:
    extract_valley_floors -> terrain attributes, valley_floor

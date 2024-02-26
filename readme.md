use with pyvalleys package

```
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
    valley_floors>/
        <huc8>_valley_floors.shp
```


```
01_dl_huc8.py
02_extract_valley_floors.py
```

todo:
- [] add snakefile
- [] move nhd preprocessing from pyvalleys to here
- [] add mask for regions we don't want to model (non river valleys - e.g central valley, death valley ...)
- [] run on state

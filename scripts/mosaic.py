import rasterio
from rasterio.merge import merge
from rasterio.features import shapes
import glob
import geopandas as gpd
import numpy as np

def process_rasters(directory_path):
    # Find all tif files
    tif_files = glob.glob(f"{directory_path}/*.tif")
    
    # Open all rasters
    src_files = [rasterio.open(f) for f in tif_files]
    
    # Merge rasters
    mosaic, out_transform = merge(src_files)
    
    # Close source files
    for src in src_files:
        src.close()
    
    # Create binary array where values > 0
    binary = np.where(mosaic[0] > 0, 1, 0)
    
    # Get metadata from first file for output
    with rasterio.open(tif_files[0]) as src:
        out_meta = src.meta.copy()
    
    # Update metadata for the merged raster
    out_meta.update({
        "height": binary.shape[0],
        "width": binary.shape[1],
        "transform": out_transform
    })
    
    # Save binary raster temporarily
    with rasterio.open("temp_binary.tif", "w", **out_meta) as dest:
        dest.write(binary.astype(rasterio.float32), 1)
    
    # Convert to vector
    with rasterio.open("temp_binary.tif") as src:
        mask = src.read(1)
        results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) in enumerate(
                shapes(mask, mask=mask > 0, transform=src.transform))
        )
        
        # Convert to GeoDataFrame
        geoms = list(results)
        gdf = gpd.GeoDataFrame.from_features(geoms)
        gdf.crs = src.crs
        
        # Dissolve all polygons into one
        gdf_dissolved = gdf.dissolve()
        
    return gdf_dissolved 

# Example usage
gdf = process_rasters("../../temp/floors/")
gdf.to_file("1805_floors.shp")

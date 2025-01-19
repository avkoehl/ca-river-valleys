"""
download polygon shapefile of land from Natural Earth
"""

import geopandas as gpd

url = "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_0_countries.zip"
world = gpd.read_file(url)
north_america = world[world["CONTINENT"] == "North America"]
north_america.to_file("./data/north_america.shp")
print("Downloaded shapefile of North America to ./data/north_america.shp")

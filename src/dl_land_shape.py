"""
This script downloads shapefiles of North America and US states from Natural Earth and NOAA, respectively.
"""

import geopandas as gpd


def dl_osm():
    url = "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_0_countries.zip"
    world = gpd.read_file(url)
    north_america = world[world["CONTINENT"] == "North America"]
    north_america.to_file("./data/north_america.shp")
    print("Downloaded shapefile of North America to ./data/north_america.shp")


def dl_us_bounds():
    url = "https://www.weather.gov/source/gis/Shapefiles/County/s_05mr24.zip"
    us = gpd.read_file(url)
    us.to_file("./data/us_states.shp")
    print("Downloaded shapefile of US states to ./data/us_states.shp")


if __name__ == "__main__":
    dl_osm()
    dl_us_bounds()

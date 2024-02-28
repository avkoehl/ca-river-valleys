# Snakefile

# input is single hucid
# 

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


rule download_data:
    input:
        hucid = "1805005"
    output:
        "data/{hucid}/dem.tif"
    shell:
        "touch data/{hucid}/dem.tif"

# rule preprocess_dem:
#      input: 
#          dem_path = "data/{hucid}/dem_raw.tif",
#          land_shapefile = "/california_mask/California.shp"
#      output:
#          "data/{hucid}/dem.tif"
#      shell:
#          "poetry run python ocean_mask.py {input} {output}"

# rule preprocess_nhd:
#     input:
#         "data/{hucid}/flowlines_raw.shp"
#     output:
#         "data/{hucid}/flowlines.shp"
#     shell:
#         "poetry run python filter_nhd.py {input} {output}"

# rule extract_valleys:
#     input:
#         dem = "data/{hucid}/dem.tif",
#         network = "data/{hucid}/flowlines.shp",
#         wbt = "~/opt/WBT"
#     params:
#         config = "configs/base.toml"
#     output:
#         terrain_dir = "data/{hucid}/terrain/",
#         valley_floors = "data/{hucid}/valley_floors.shp"
#     shell:
#         "poetry run python extract_valleys.py {input.dem} {input.network} {params.config} {output.terrain_dir} {output.valley_floors}"

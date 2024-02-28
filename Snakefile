# Snakefile

rule download_data:
    params:
        hucid = '1801010902'
    output:
        "data/1801010902/1801010902-dem_raw.tif",
	"data/1801010902/1801010902-flowlines_raw.shp"
    shell:
        "poetry run python src/download_huc.py {params.hucid} {output}"

rule preprocess_dem:
      input: 
          dem_path = "data/1801010902/1801010902-dem_raw.tif",
          land_shapefile = "california_mask/California.shp"
      output:
          "data/1801010902/1801010902-dem.tif"
      shell:
          "poetry run python src/ocean_mask.py {input.dem_path} {input.land_shapefile} {output}"

rule preprocess_nhd:
     input:
         "data/1801010902/1801010902-flowlines_raw.shp"
     output:
         "data/1801010902/1801010902-flowlines.shp"
     shell:
         "poetry run python src/filter_nhd.py {input} {output}"

rule extract_valleys:
     input:
         dem = "data/1801010902/1801010902-dem.tif",
         network = "data/1801010902/1801010902-flowlines.shp"
     params:
         config = "configs/base.toml",
         wbt = os.path.expanduser("~/opt/WBT")
     output:
         terrain_dir = directory("data/1801010902/terrain/"),
         valley_floors = "data/1801010902/1801010902-valley_floors.shp"
     shell:
         "poetry run python src/valley_floors.py {input.dem} {input.network} {params.wbt} {params.config} {output.terrain_dir} {output.valley_floors}"

rule all:
    input: 
        "data/1801010902/1801010902-valley_floors.shp"

# Snakefile
CUSTOM_HUCIDS = ['1805000203']

DEMO_HUCIDS = ['1801010902', '1605030102']
CA_HUC8_HUCIDS= ['1801010902', '1801010805']

rule all:
    input: 
        expand("data/{hucid}/{hucid}-valley_floors.shp", hucid=CA_HUC8_HUCIDS)

rule demo_all:
    input:
        expand("data/{hucid}/{hucid}-valley_floors.shp", hucid=DEMO_HUCIDS)

rule custom_all:
    input:
        expand("data/{hucid}/{hucid}-valley_floors.shp", hucid=CUSTOM_HUCIDS)

rule download_data:
    params:
        hucid = '{hucid}'
    output:
        "data/{hucid}/{hucid}-dem_raw.tif",
	"data/{hucid}/{hucid}-flowlines_raw.shp"
    shell:
        "poetry run python src/download_huc.py {params.hucid} {output}"

rule preprocess_dem:
      input: 
          dem_path = "data/{hucid}/{hucid}-dem_raw.tif",
          land_shapefile = "california_mask/California.shp"
      output:
          "data/{hucid}/{hucid}-dem.tif"
      shell:
          "poetry run python src/ocean_mask.py {input.dem_path} {input.land_shapefile} {output}"

rule preprocess_nhd:
     input:
         "data/{hucid}/{hucid}-flowlines_raw.shp"
     output:
         "data/{hucid}/{hucid}-flowlines.shp"
     shell:
         "poetry run python src/filter_nhd.py {input} {output}"

rule extract_valleys:
     input:
         dem = "data/{hucid}/{hucid}-dem.tif",
         network = "data/{hucid}/{hucid}-flowlines.shp"
     params:
         config = "configs/base.toml",
         wbt = os.path.expanduser("~/opt/WBT")
     output:
         terrain_dir = directory("data/{hucid}/terrain_attributes/"),
         valley_floors = "data/{hucid}/{hucid}-valley_floors.shp"
     shell:
         "poetry run python -m pyvalleys {input.dem} {input.network} {params.config} {params.wbt} {output.terrain_dir} {output.valley_floors}"


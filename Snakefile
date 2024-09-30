# Snakefile
import os

output_base = '/Volumes/koehl_4tb/data-20240929/' 

os.environ["HYRIVER_CACHE_DISABLE"] = "true"

import pandas as pd
huc10s = pd.read_csv("huc10s.csv")
huc10s = huc10s['huc10']
sample = huc10s.sample(150, random_state=14)


DEMO_HUCIDS = ['180500040803', '180500050303', '180600060101', '180901020208', '180201280202']

HUCIDS= ['1805000203']

rule all:
    input: 
        expand(output_base + "{hucid}/{hucid}-floors.tif", hucid=sample)

rule demo_all:
    input:
        expand(output_base + "{hucid}/{hucid}-floors.tif", hucid=HUCIDS)


rule download_data:
    params:
        hucid = '{hucid}'
    output:
        output_base + "{hucid}/{hucid}-dem_raw.tif",
	output_base + "{hucid}/{hucid}-flowlines_raw.shp"
    shell:
        "poetry run python src/download_huc.py {params.hucid} {output}"

rule preprocess_dem:
      input: 
          dem_path = output_base + "{hucid}/{hucid}-dem_raw.tif",
          land_shapefile = "california_mask/California.shp"
      output:
          output_base + "{hucid}/{hucid}-dem.tif"
      shell:
          "poetry run python src/ocean_mask.py {input.dem_path} {input.land_shapefile} {output}"

rule preprocess_nhd:
     input:
         output_base + "{hucid}/{hucid}-flowlines_raw.shp"
     output:
         output_base + "{hucid}/{hucid}-flowlines.shp"
     shell:
         "poetry run python src/filter_nhd.py {input} {output}"

rule extract_valleys:
     input:
         dem = output_base + "{hucid}/{hucid}-dem.tif",
         network = output_base + "{hucid}/{hucid}-flowlines.shp"
     params:
         param = "configs/params.toml",
         wbt = os.path.expanduser("~/opt/WBT"),
	 log_file = output_base + "{hucid}/run.log"
     output:
         terrain_dir = directory(output_base + "{hucid}/derived/"),
         ofile = output_base + "{hucid}/{hucid}-floors.tif/"
     shell:
         "poetry run python -m valleyfloor --dem {input.dem} --flowlines {input.network} --param {params.param}  --wbt {params.wbt} --terrain_dir {output.terrain_dir} --ofile {output.ofile} --enable-logging --log-file {params.log_file}" 


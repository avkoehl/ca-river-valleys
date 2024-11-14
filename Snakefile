# Snakefile
import os

output_base = '../outputs/'

os.environ["HYRIVER_CACHE_DISABLE"] = "true"

import pandas as pd
huc10s = pd.read_csv("huc10s.csv")
huc10s = huc10s['huc10']
sample = huc10s.sample(5, random_state=14)


DEMO_HUCIDS = ['180500040803', '180500050303', '180600060101', '180901020208', '180201280202']

HUCIDS= ['1805000203']

rule all:
    input: 
        expand(output_base + "20241113/{hucid}-floors.tif", hucid=sample)

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
         param_file = "configs/params_10m.toml",
	       working_dir = output_base + "{hucid}_working_dir",
	       flowlines_ofile = output_base + "20241113/{hucid}-flowlines.shp",
	       log_file = output_base + "20241113/{hucid}-run.log"
     output:
	       output_base + "20241113/{hucid}-floors.tif"
     shell:
         "poetry run python -m valleyx --dem_file {input.dem} --flowlines_file {input.network} --working_dir {params.working_dir} --param_file {params.param_file} --floor_ofile {output} --flowlines_ofile {params.flowlines_ofile} --enable_logging --log_file {params.log_file}" 


# load list of all the huc10s, compare with list of all the completed

from glob import glob

import pandas as pd


floors_dir = "/dsl/valleys/cleanup/floors/"
manifest_file = "../data/huc_manifest/huc_manifest.csv"

hucs = pd.read_csv(manifest_file)

floors_files = glob(f"{floors_dir}*-floors.tif")
completed = []
for f in floors_files:
    huc10 = f.split('/')[-1].split('-')[0]
    completed.append(huc10)

# possible
huc10s = hucs.loc[hucs['level'] == 'huc10']
huc10s['hucid'] = huc10s['hucid'].astype('str')
huc10s = huc10s.loc[huc10s['hucid'].str.startswith('18')]

# missing
missing = set(huc10s['hucid']) - set(completed)



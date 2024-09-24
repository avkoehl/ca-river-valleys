import sys

import geopandas as gpd

from utils import setup_output

def filter_nhd_flowlines(nhd_network):
    # remove small headwater streams < 1km and non-river features
    # check for required columns
    required = ['StartFlag', 'FTYPE', 'geometry', 'LENGTHKM']

    if not all([col in nhd_network.columns for col in required]):
        raise ValueError('Input NHDPlus dataset must contain columns: StartFlag, FTYPE, geometry, LENGTHKM')

    # filter flow lines
    nhd_network = nhd_network.loc[nhd_network['FTYPE'] == 'StreamRiver']
    nhd_network = nhd_network.loc[~((nhd_network['StartFlag'] == 1) & (nhd_network['LENGTHKM'] < 1))]

    # keep only if Linestring
    nhd_network = nhd_network[nhd_network.geometry.type == 'LineString']
    return nhd_network

def main():
    nhd_file = sys.argv[1]
    ofile = sys.argv[2]

    flowlines = gpd.read_file(nhd_file)
    flowlines = filter_nhd_flowlines(flowlines)

    setup_output(ofile)
    flowlines.to_file(ofile)

if __name__ == "__main__":
    main()

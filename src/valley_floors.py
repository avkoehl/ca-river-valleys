import os
import sys

import pandas as pd

from pyvalleys.workflow import valley_floors

def main():
    dem_file = sys.argv[1]
    network_file = sys.argv[2]

    wbt = sys.argv[3]

    config = sys.argv[4]
    terrain_dir = sys.argv[5]
    ofile = sys.argv[6]

    valley_floors(dem_file, network_file, config, wbt, terrain_dir, ofile)

if __name__ == "__main__":
    main()

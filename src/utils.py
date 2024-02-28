import os

def setup_output(filename):
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.make_dirs(directory)

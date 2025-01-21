import whitebox

wbt = whitebox.WhiteboxTools()
print("WhiteboxTools initialized succesfuly")

with open("./data/whitebox_init.txt", "w") as f:
    f.write("WhiteboxTools initialized succesfuly")
    f.write(wbt.version())

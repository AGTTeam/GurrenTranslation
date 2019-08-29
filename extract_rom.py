import os
import shutil

outfolder = "extract/"

if not os.path.isfile("ndstool.exe"):
    print("[ERROR] ndstool.exe not found")
else:
    print("Extracting ROM ...")
    if os.path.isdir(outfolder):
        shutil.rmtree(outfolder)
    os.mkdir(outfolder)
    os.system("ndstool -x rom.nds -9 extract/arm9.bin -7 extract/arm7.bin -y9 extract/y9.bin -y7 extract/y7.bin -t extract/banner.bin -h extract/header.bin -d extract/data -y extract/overlay")

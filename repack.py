import shutil
import os
import common
import sys

extractfolder = "extract/"
infolder = "work_NFP/"
outfolder = "repack/"
if os.path.isdir(outfolder):
    shutil.rmtree(outfolder)
os.mkdir(outfolder)
nfponly = len(sys.argv) == 2 and sys.argv[1] == "nfp"

# Create the folders and copy the files
os.mkdir(outfolder + "data")
os.mkdir(outfolder + "overlay")
shutil.copyfile(extractfolder + "arm7.bin", outfolder + "arm7.bin")
shutil.copyfile(extractfolder + "arm9.bin", outfolder + "arm9.bin")
shutil.copyfile(extractfolder + "banner.bin", outfolder + "banner.bin")
shutil.copyfile(extractfolder + "header.bin", outfolder + "header.bin")
shutil.copyfile(extractfolder + "y7.bin", outfolder + "y7.bin")
shutil.copyfile(extractfolder + "y9.bin", outfolder + "y9.bin")

if not nfponly:
    os.system("python repack_spc.py")
    os.system("python repack_bin.py")
    os.system("python repack_3dg.py")
    os.system("python repack_kpc.py")

# Repack NFP
print("Repacking NFP ...")
for file in os.listdir(infolder):
    subfiles = os.listdir(infolder + file)
    filenum = len(subfiles)
    # Data starts at header (80 bytes) + entries (24 bytes each)
    datapos = 80 + (24 * filenum)
    # The file list is padded with 0s if it doesn't start at a multiple of 16
    datapos += datapos % 16
    print(" Repacking " + file + " with " + str(filenum) + " files ...")
    with open(outfolder + "data/" + file, "wb") as f:
        common.writeString(f, "NFP2.0 (c)NOBORI 1997-2006")
        common.writeZero(f, 26)
        common.writeInt(f, filenum)
        common.writeInt(f, 0x50)
        common.writeInt(f, datapos)
        for i in range(filenum):
            subfile = subfiles[i]
            subfilepath = infolder + file + "/" + subfile
            filesize = os.path.getsize(subfilepath)
            f.seek(80 + (24 * i))
            common.writeString(f, subfile)
            if len(subfile) < 16:
                common.writeZero(f, 16 - len(subfile))
            common.writeInt(f, datapos)
            common.writeInt(f, filesize * 4)
            f.seek(datapos)
            with open(subfilepath, "rb") as newf:
                f.write(newf.read(filesize))
            datapos += filesize

# Repack ROM
print("Repacking ROM ...")
if not os.path.isfile("ndstool.exe"):
    print("[ERROR] ndstool.exe not found")
else:
    os.system("ndstool -c rom_patched.nds -9 repack/arm9.bin -7 repack/arm7.bin -y9 repack/y9.bin -y7 repack/y7.bin -t repack/banner.bin -h repack/header.bin -d repack/data -y repack/overlay")
    print("Done!")

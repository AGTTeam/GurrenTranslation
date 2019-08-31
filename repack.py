import os
import shutil
import sys
import common

romfile = "data/rom.nds"
rompatch = "data/rom_patched.nds"
patchfile = "data/patch.xdelta"
extractfolder = "data/extract/"
debfolder = "data/extract_NFP/"
infolder = "data/work_NFP/"
outfolder = "data/repack/"
if os.path.isdir(outfolder):
    shutil.rmtree(outfolder)
os.mkdir(outfolder)
all = len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "-deb")

# Create the folders and copy the files
os.mkdir(outfolder + "data")
os.mkdir(outfolder + "overlay")
shutil.copyfile(extractfolder + "arm7.bin", outfolder + "arm7.bin")
shutil.copyfile(extractfolder + "arm9.bin", outfolder + "arm9.bin")
shutil.copyfile(extractfolder + "banner.bin", outfolder + "banner.bin")
shutil.copyfile(extractfolder + "header.bin", outfolder + "header.bin")
shutil.copyfile(extractfolder + "y7.bin", outfolder + "y7.bin")
shutil.copyfile(extractfolder + "y9.bin", outfolder + "y9.bin")

# Repack the font
if not os.path.isfile("NerdFontTerminatoR.exe"):
    print("[ERROR] NerdFontTerminatoR.exe not found")
elif all or "-bin" in sys.argv or "-spc" in sys.argv:
    os.system("python repack_font.py")

if all or "-spc" in sys.argv:
    os.system("python repack_spc.py")
if all or "-bin" in sys.argv:
    os.system("python repack_bin.py")
if all or "-3dg" in sys.argv:
    os.system("python repack_3dg.py")
if all or "-kpc" in sys.argv:
    os.system("python repack_kpc.py")
if all or "-vsc" in sys.argv:
    os.system("python repack_vsc.py")
if all or "-yce" in sys.argv:
    os.system("python repack_yce.py")

if "-deb" in sys.argv:
    shutil.copyfile(debfolder + "SPC.NFP/S_DEBUG.SPC", infolder + "SPC.NFP/S_MAIN.SPC")
else:
    shutil.copyfile(debfolder + "SPC.NFP/S_MAIN.SPC", infolder + "SPC.NFP/S_MAIN.SPC")

# Repack NFP
print("Repacking NFP ...")
for file in os.listdir(infolder):
    subfiles = os.listdir(infolder + file)
    filenum = len(subfiles)
    # Data starts at header (80 bytes) + entries (24 bytes each)
    datapos = 80 + (24 * filenum)
    # The file list is padded with 0s if it doesn't start at a multiple of 16
    datapos += datapos % 16
    print(" Repacking", file, "with", filenum, "files ...")
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

# Patch banner.bin
print("Patching banner.bin ...")
title = "Tengen Toppa\nGurren Lagann\nKonami Digital Entertainment"
with open(outfolder + "banner.bin", "r+b") as f:
    common.patchBanner(f, title)

# Repack ROM
if not os.path.isfile("ndstool.exe"):
    print("[ERROR] ndstool.exe not found")
else:
    print("Repacking ROM ...")
    os.system("ndstool -c {rom} -9 {folder}arm9.bin -7 {folder}arm7.bin -y9 {folder}y9.bin -y7 {folder}y7.bin -t {folder}banner.bin -h {folder}header.bin -d {folder}data -y {folder}overlay".
              format(rom=rompatch, folder=outfolder))
    # Create xdelta patch
    if not os.path.isfile("xdelta.exe"):
        print("[ERROR] xdelta.exe not found")
    else:
        print("Creating patch ...")
        os.system("xdelta -f -e -s {rom} {rompatch} {patch}".format(rom=romfile, rompatch=rompatch, patch=patchfile))
        print("All done!")

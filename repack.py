import os
import sys
import common

romfile = "data/rom.nds"
rompatch = "data/rom_patched.nds"
patchfile = "data/patch.xdelta"
extractfolder = "data/extract/"
debfolder = "data/extract_NFP/"
infolder = "data/work_NFP/"
outfolder = "data/repack/"
common.makeFolder(outfolder)
all = len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "-deb")

# Create the folders and copy the files
common.makeFolder(outfolder + "data")
common.makeFolder(outfolder + "overlay")
common.copyFile(extractfolder + "arm7.bin", outfolder + "arm7.bin")
common.copyFile(extractfolder + "arm9.bin", outfolder + "arm9.bin")
common.copyFile(extractfolder + "banner.bin", outfolder + "banner.bin")
common.copyFile(extractfolder + "header.bin", outfolder + "header.bin")
common.copyFile(extractfolder + "y7.bin", outfolder + "y7.bin")
common.copyFile(extractfolder + "y9.bin", outfolder + "y9.bin")

# Repack the font
if not os.path.isfile("NerdFontTerminatoR.exe"):
    print("[ERROR] NerdFontTerminatoR.exe not found")
elif all or "-bin" in sys.argv or "-spc" in sys.argv:
    common.execute("python repack_font.py")

if all or "-spc" in sys.argv:
    common.execute("python repack_spc.py")
if all or "-bin" in sys.argv:
    common.execute("python repack_bin.py")
if all or "-3dg" in sys.argv:
    common.execute("python repack_3dg.py")
if all or "-kpc" in sys.argv:
    common.execute("python repack_kpc.py")
if all or "-vsc" in sys.argv:
    common.execute("python repack_vsc.py")
if all or "-yce" in sys.argv:
    common.execute("python repack_yce.py")

if "-deb" in sys.argv:
    common.copyFile(debfolder + "SPC.NFP/S_DEBUG.SPC", infolder + "SPC.NFP/S_MAIN.SPC")
else:
    common.copyFile(debfolder + "SPC.NFP/S_MAIN.SPC", infolder + "SPC.NFP/S_MAIN.SPC")

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
    with common.Stream(outfolder + "data/" + file, "wb") as f:
        f.writeString("NFP2.0 (c)NOBORI 1997-2006")
        f.writeZero(26)
        f.writeInt(filenum)
        f.writeInt(0x50)
        f.writeInt(datapos)
        for i in range(filenum):
            subfile = subfiles[i]
            subfilepath = infolder + file + "/" + subfile
            filesize = os.path.getsize(subfilepath)
            f.seek(80 + (24 * i))
            f.writeString(subfile)
            if len(subfile) < 16:
                f.writeZero(16 - len(subfile))
            f.writeInt(datapos)
            f.writeInt(filesize * 4)
            f.seek(datapos)
            with open(subfilepath, "rb") as newf:
                f.write(newf.read(filesize))
            datapos += filesize

# Patch banner.bin
print("Patching banner.bin ...")
title = "Tengen Toppa\nGurren Lagann\nKonami Digital Entertainment"
with common.Stream(outfolder + "banner.bin", "r+b") as f:
    common.patchBanner(f, title)

# Repack ROM
if not os.path.isfile("ndstool.exe"):
    print("[ERROR] ndstool.exe not found")
else:
    print("Repacking ROM ...")
    common.execute("ndstool -c {rom} -9 {folder}arm9.bin -7 {folder}arm7.bin -y9 {folder}y9.bin -y7 {folder}y7.bin -t {folder}banner.bin -h {folder}header.bin -d {folder}data -y {folder}overlay".
                   format(rom=rompatch, folder=outfolder), False)
    # Create xdelta patch
    if not os.path.isfile("xdelta.exe"):
        print("[ERROR] xdelta.exe not found")
    else:
        print("Creating patch ...")
        common.execute("xdelta -f -e -s {rom} {rompatch} {patch}".format(rom=romfile, rompatch=rompatch, patch=patchfile), False)
        print("All done!")

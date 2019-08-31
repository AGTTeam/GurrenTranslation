import os
import common

romfile = "data/rom.nds"
extractfolder = "data/extract/"
infolder = "data/extract/data/"
outfolder = "data/extract_NFP/"
common.makeFolder(outfolder)
workfolder = "data/work_NFP/"

if not os.path.isfile("ndstool.exe"):
    print("[ERROR] ndstool.exe not found")
else:
    print("Extracting ROM ...")
    common.makeFolder(extractfolder)
    common.execute("ndstool -x {rom} -9 {folder}arm9.bin -7 {folder}arm7.bin -y9 {folder}y9.bin -y7 {folder}y7.bin -t {folder}banner.bin -h {folder}header.bin -d {folder}data -y {folder}overlay".
                   format(rom=romfile, folder=extractfolder), False)

    print("Extracting NFP ...")
    for file in os.listdir(infolder):
        print(" Processing", file, "...")
        common.makeFolder(outfolder + file)
        with common.Stream(infolder + file, "rb") as f:
            f.seek(52)  # Header: NFP2.0 (c)NOBORI 1997-2006
            filenum = f.readInt()
            f.seek(4, 1)  # Always 0x50
            datastart = f.readInt()
            f.seek(16, 1)  # All 0
            print("  Found", filenum, "files, data starting at", datastart)
            for i in range(filenum):
                # Filenames are always 16 bytes long, padded with 0s
                subname = f.readString(16)
                # Read starting position and size (multiplied by 4)
                startpos = f.readInt()
                size = f.readInt() // 4
                # Extract the file
                if common.debug:
                    print("  Extracting", subname, "starting at", startpos, "with size", size)
                savepos = f.tell()
                f.seek(startpos)
                with common.Stream(outfolder + file + "/" + subname, "wb") as newf:
                    newf.write(f.read(size))
                f.seek(savepos)

    # Copy everything to the work folder
    common.copyFolder(outfolder, workfolder)

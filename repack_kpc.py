import os
import game
from hacktools import common


def run():
    infolder = "data/extract_NFP/NFP2D.NFP/"
    workfolder = "data/work_KPC/"
    outfolder = "data/work_NFP/NFP2D.NFP/"
    common.copyFolder(infolder, outfolder)

    common.logMessage("Repacking KPC from", workfolder, "...")
    files = common.getFiles(infolder, ".KPC")
    for file in common.showProgress(files):
        pngname = file.replace(".KPC", ".png")
        if not os.path.isfile(workfolder + pngname):
            common.copyFile(infolder + file, outfolder + file)
            continue
        common.logDebug("Processing", file, "...")
        with common.Stream(infolder + file, "rb") as fin:
            with common.Stream(outfolder + file, "wb") as f:
                # Find palette offset
                fin.seek(9)
                palcompressed = fin.readByte() == 1
                fin.seek(2, 1)
                width = fin.readUShort() * 8
                height = fin.readUShort() * 8
                fin.seek(128)
                palsize = fin.readUInt()
                paloffset = fin.readUInt()
                # Read palette
                fin.seek(paloffset)
                if palcompressed:
                    paldata = common.decompress(fin, palsize)
                else:
                    paldata = fin.read(palsize)
                # Fix transparency for EQ_M0* files since their palette colors 0 and 1 are the same.
                tiles, maps = game.readMappedImage(workfolder + pngname, width, height, paldata, file.startswith("EQ_M0"))
                # Copy the header
                fin.seek(0)
                f.write(fin.read(192))
                # Write map data
                mapstart = f.tell()
                for map in maps:
                    mapdata = (map[0] << 12) + (map[1] << 11) + (map[2] << 10) + map[3]
                    f.writeUShort(mapdata)
                mapend = f.tell()
                f.writeByte(0)
                # Write tile data
                tilestart = f.tell()
                for tile in tiles:
                    for i in range(32):
                        index2 = tile[i * 2]
                        index1 = tile[i * 2 + 1]
                        f.writeByte(((index1) << 4) | index2)
                tileend = f.tell()
                f.writeByte(0)
                # Write palette
                palstart = f.tell()
                f.write(paldata)
                palend = f.tell()
                f.writeByte(0)
                # Write header data
                f.seek(9)
                f.writeByte(0)
                f.writeByte(0)
                f.writeByte(0)
                f.seek(16)
                f.writeUInt(mapend - mapstart)
                f.writeUInt(mapstart)
                f.seek(92)
                f.writeUInt(tileend - tilestart)
                f.writeUInt(tilestart)
                f.seek(128)
                f.writeUInt(palend - palstart)
                f.writeUInt(palstart)
    common.logMessage("Done!")

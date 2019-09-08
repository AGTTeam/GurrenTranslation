import os
import game
from hacktools import common


def run():
    infolder = "data/extract_NFP/NFP2D.NFP/"
    workfolder = "data/work_VSC/"
    outfolder = "data/work_NFP/NFP2D.NFP/"

    common.logMessage("Repacking VSC from", workfolder, "...")
    files = common.getFiles(infolder, ".VSC")
    for file in common.showProgress(files):
        pngname = file.replace(".VSC", ".png")
        if not os.path.isfile(workfolder + pngname):
            common.copyFile(infolder + file, outfolder + file)
            continue
        common.logDebug("Processing", file, "...")
        with common.Stream(infolder + file, "rb") as fin:
            with common.Stream(outfolder + file, "wb") as f:
                # Read header
                fin.seek(16)
                bpp = 4 if fin.readUInt() == 1 else 8
                width = fin.readUInt()
                height = fin.readUInt()
                fin.seek(4, 1)
                mapsize = fin.readUInt()
                fin.seek(4, 1)
                tilesize = fin.readUInt()
                mapdata = fin.read(mapsize)
                fin.seek(tilesize, 1)
                fin.seek(24, 1)
                palnum = fin.readUShort()
                fin.seek(4, 1)
                paloffset = fin.tell()
                paldata = fin.read(palnum * 32)
                tiles, maps = game.readMappedImage(workfolder + pngname, width, height, paldata)
                # Copy the header
                fin.seek(0)
                f.write(fin.read(44))
                # Write map data
                mapstart = f.tell()
                for map in maps:
                    mapdata = (map[0] << 12) + (map[1] << 11) + (map[2] << 10) + map[3]
                    f.writeUShort(mapdata)
                mapend = f.tell()
                # Write tile data
                tilestart = f.tell()
                for tile in tiles:
                    for i in range(32 if bpp == 4 else 64):
                        if bpp == 8:
                            f.writeByte(tile[i])
                        else:
                            index2 = tile[i * 2]
                            index1 = tile[i * 2 + 1]
                            f.writeByte(((index1) << 4) | index2)
                tileend = f.tell()
                # Copy the palette
                fin.seek(paloffset - 30)
                f.write(fin.read(30 + palnum * 32))
                palend = f.tell()
                f.writeZero(16 - palend % 16)
                # Write the new header data
                f.seek(8)
                f.writeUInt(palend)
                f.seek(36)
                f.writeUInt(mapend - mapstart)
                f.writeUInt(tileend - tilestart)
    common.logMessage("Done!")

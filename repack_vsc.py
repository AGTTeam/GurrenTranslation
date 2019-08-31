import os
import shutil
import common
import common_game as game

vscin = "data/extract_NFP/NFP2D.NFP/"
vscwork = "data/work_VSC/"
vscout = "data/work_NFP/NFP2D.NFP/"

print("Repacking VSC ...")
for file in os.listdir(vscin):
    if not file.endswith(".VSC"):
        continue
    pngname = file.replace(".VSC", ".png")
    if not os.path.isfile(vscwork + pngname):
        shutil.copyfile(vscin + file, vscout + file)
    else:
        if common.debug:
            print("Processing", file, "...")
        with common.Stream(vscin + file, "rb") as fin:
            with common.Stream(vscout + file, "wb") as f:
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
                tiledata = fin.read(tilesize)
                fin.seek(24, 1)
                palnum = fin.readUShort()
                fin.seek(4, 1)
                paloffset = fin.tell()
                paldata = fin.read(palnum * 32)
                tiles, maps = game.readMappedImage(vscwork + pngname, width, height, paldata)
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

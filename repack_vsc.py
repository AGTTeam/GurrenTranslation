import shutil
import os
import common

vscin = "extract_NFP/NFP2D.NFP/"
vscwork = "work_VSC/"
vscout = "work_NFP/NFP2D.NFP/"

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
        with open(vscin + file, "rb") as fin:
            with open(vscout + file, "wb") as f:
                # Read header
                fin.seek(16)
                bpp = 4 if common.readUInt(fin) == 1 else 8
                width = common.readUInt(fin)
                height = common.readUInt(fin)
                fin.seek(4, 1)
                mapsize = common.readUInt(fin)
                fin.seek(4, 1)
                tilesize = common.readUInt(fin)
                mapdata = fin.read(mapsize)
                tiledata = fin.read(tilesize)
                fin.seek(24, 1)
                palnum = common.readUShort(fin)
                fin.seek(4, 1)
                paloffset = fin.tell()
                paldata = fin.read(palnum * 32)
                tiles, maps = common.readMappedImage(vscwork + pngname, width, height, paldata)
                # Copy the header
                fin.seek(0)
                f.write(fin.read(44))
                # Write map data
                mapstart = f.tell()
                for map in maps:
                    mapdata = (map[0] << 12) + (map[1] << 11) + (map[2] << 10) + map[3]
                    common.writeUShort(f, mapdata)
                mapend = f.tell()
                # Write tile data
                tilestart = f.tell()
                for tile in tiles:
                    for i in range(32 if bpp == 4 else 64):
                        if bpp == 8:
                            common.writeByte(f, tile[i])
                        else:
                            index2 = tile[i * 2]
                            index1 = tile[i * 2 + 1]
                            common.writeByte(f, ((index1) << 4) | index2)
                tileend = f.tell()
                # Copy the palette
                fin.seek(paloffset - 30)
                f.write(fin.read(30 + palnum * 32))
                palend = f.tell()
                common.writeZero(f, 16 - palend % 16)
                # Write the new header data
                f.seek(8)
                common.writeUInt(f, palend)
                f.seek(36)
                common.writeUInt(f, mapend - mapstart)
                common.writeUInt(f, tileend - tilestart)

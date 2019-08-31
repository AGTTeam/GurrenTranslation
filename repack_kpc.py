import os
import common
import common_game as game

kpcin = "data/extract_NFP/NFP2D.NFP/"
kpcwork = "data/work_KPC/"
kpcout = "data/work_NFP/NFP2D.NFP/"
common.makeFolder(kpcout)

print("Repacking KPC ...")
for file in os.listdir(kpcin):
    if not file.endswith(".KPC") and not file.endswith(".KPC"):
        common.copyFile(kpcin + file, kpcout + file)
    pngname = file.replace(".KPC", ".png")
    if not os.path.isfile(kpcwork + pngname):
        common.copyFile(kpcin + file, kpcout + file)
    else:
        if common.debug:
            print("Processing", file, "...")
        with common.Stream(kpcin + file, "rb") as fin:
            with common.Stream(kpcout + file, "wb") as f:
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
                palettes = []
                if palcompressed:
                    paldata = common.decompress(fin, palsize)
                else:
                    paldata = fin.read(palsize)
                # Fix transparency for EQ_M0* files since their palette colors 0 and 1 are the same.
                tiles, maps = game.readMappedImage(kpcwork + pngname, width, height, paldata, file.startswith("EQ_M0"))
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

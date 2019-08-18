import shutil
import os
import common
import struct
from PIL import Image

kpcin = "extract_NFP/NFP2D.NFP/"
kpcwork = "work_KPC/"
kpcout = "work_NFP/NFP2D.NFP/"
if os.path.isdir(kpcout):
    shutil.rmtree(kpcout)
os.mkdir(kpcout)

print("Repacking KPC ...")

for file in os.listdir(kpcin):
    if not file.endswith(".KPC") and not file.endswith(".KPC"):
        shutil.copyfile(kpcin + file, kpcout + file)
    pngname = file.replace(".KPC", ".png")
    if not os.path.isfile(kpcwork + pngname):
        shutil.copyfile(kpcin + file, kpcout + file)
    else:
        print("Processing " + file + " ...")
        with open(kpcin + file, "rb") as fin:
            with open(kpcout + file, "wb") as f:
                # Find palette offset
                fin.seek(9)
                palcompressed = common.readByte(fin) == 1
                fin.seek(2, 1)
                width = common.readUShort(fin) * 8
                height = common.readUShort(fin) * 8
                fin.seek(128)
                palsize = common.readUInt(fin)
                paloffset = common.readUInt(fin)
                # Read palette
                fin.seek(paloffset)
                palettes = []
                if palcompressed:
                    paldata = common.decompress(fin, palsize)
                else:
                    paldata = fin.read(palsize)
                for j in range(len(paldata) // 32):
                    palette = []
                    for i in range(0, 32, 2):
                        p = struct.unpack("<H", paldata[j*32+i:j*32+i+2])[0]
                        palette.append(common.readPalette(p))
                    palettes.append(palette)
                # Read the image
                img = Image.open(kpcwork + pngname)
                img = img.convert("RGBA")
                pixels = img.load()
                # Split image into tiles and maps
                tiles = []
                maps = []
                tileheight = tilewidth = 8
                i = j = 0
                while i < height:
                    tilecolors = []
                    for i2 in range(tileheight):
                        for j2 in range(tilewidth):
                            tilecolors.append(pixels[j + j2, i + i2])
                    pal = common.findBestPalette(palettes, tilecolors)
                    tile = []
                    for tilecolor in tilecolors:
                        tile.append(common.getPaletteIndex(palettes[pal], tilecolor))
                    tiles.append(tile)
                    maps.append((pal, 0, 0, len(tiles) - 1))
                    j += tilewidth
                    if j >= width:
                        j = 0
                        i += tileheight
                # Copy the header
                fin.seek(0)
                f.write(fin.read(192))
                # Write map data
                mapstart = f.tell()
                for map in maps:
                    mapdata = (map[0] << 12) + (map[1] << 11) + (map[2] << 10) + map[3]
                    common.writeUShort(f, mapdata)
                mapend = f.tell()
                common.writeByte(f, 0)
                # Write tile data
                tilestart = f.tell()
                for tile in tiles:
                    for i in range(32):
                        index2 = tile[i*2]
                        index1 = tile[i*2+1]
                        common.writeByte(f, ((index1) << 4) | index2)
                tileend = f.tell()
                common.writeByte(f, 0)
                # Write palette
                palstart = f.tell()
                f.write(paldata)
                palend = f.tell()
                common.writeByte(f, 0)
                # Write header data
                f.seek(9)
                common.writeByte(f, 0)
                common.writeByte(f, 0)
                common.writeByte(f, 0)
                f.seek(16)
                common.writeUInt(f, mapend - mapstart)
                common.writeUInt(f, mapstart)
                f.seek(92)
                common.writeUInt(f, tileend - tilestart)
                common.writeUInt(f, tilestart)
                f.seek(128)
                common.writeUInt(f, palend - palstart)
                common.writeUInt(f, palstart)

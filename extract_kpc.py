import os
import shutil
import common
import struct
from PIL import Image, ImageOps

infolder = "extract_NFP/NFP2D.NFP/"
outfolder = "work_KPC/"
if os.path.isdir(outfolder):
    shutil.rmtree(outfolder)
os.mkdir(outfolder)

for file in os.listdir(infolder):
    if not file.endswith(".KPC"):
        continue
    # if file != "M09_2_B02.KPC":
    #     continue
    print("Processing " + file + " ...")
    with open(infolder + file, "rb") as f:
        # Read header
        f.seek(4)
        bits = []
        for i in range(5):
            bits.append(common.readByte(f))
        palcompressed = common.readByte(f) == 1
        mapcompressed = common.readByte(f) == 1
        tilecompressed = common.readByte(f) == 1
        width = common.readUShort(f) * 8
        height = common.readUShort(f) * 8
        mapsize = common.readUInt(f)
        mapoffset = common.readUInt(f)
        f.seek(92)
        tilesize = common.readUInt(f)
        tileoffset = common.readUInt(f)
        f.seek(124)
        unk = common.readUInt(f)
        palsize = common.readUInt(f)
        paloffset = common.readUInt(f)
        if common.debug:
            print(" width: " + str(width) + " height: " + str(height))
            print(" mapsize: " + str(mapsize) + " mapoffset: " + str(mapoffset))
            print(" tilesize: " + str(tilesize) + " tileoffset: " + str(tileoffset))
            print(" palsize: " + str(palsize) + " paloffset: " + str(paloffset))
            print(" palcompressed: " + str(palcompressed) + " mapcompressed: " + str(mapcompressed) + " tilecompressed: " + str(tilecompressed))
            print(" bits: " + str(bits) + " unk: " + str(unk))
        # Read palette
        f.seek(paloffset)
        palettes = []
        if palcompressed:
            paldata = common.decompress(f, palsize)
        else:
            paldata = f.read(palsize)
        for j in range(len(paldata) // 32):
            palette = []
            for i in range(0, 32, 2):
                p = struct.unpack("<H", paldata[j*32+i:j*32+i+2])[0]
                palette.append(common.readPalette(p))
            palettes.append(palette)
        if common.debug:
            print(" Loaded " + str(len(palettes)) + " palettes")
        # Export the image
        img = Image.new("RGBA", (width + 40, max(height, ((len(palettes) * 16) // 8) * 5)), (0, 0, 0, 0))
        pixels = img.load()
        # Read map data
        f.seek(mapoffset)
        if mapcompressed:
            mapdata = common.decompress(f, mapsize)
        else:
            mapdata = f.read(mapsize)
        maps = []
        for i in range(0, len(mapdata), 2):
            map = struct.unpack("<h", mapdata[i:i+2])[0]
            pal = (map >> 12) & 0xF
            xflip = (map >> 10) & 1
            yflip = (map >> 11) & 1
            tile = map & 0x3FF
            maps.append((pal, xflip, yflip, tile))
        if common.debug:
            print(" Loaded " + str(len(maps)) + " maps")
        # Read tile data
        tiles = []
        f.seek(tileoffset)
        if tilecompressed:
            tiledata = common.decompress(f, tilesize)
        else:
            tiledata = f.read(tilesize)
        for i in range(len(tiledata) // 32):
            singletile = []
            for j in range(64):
                x = i * 64 + j
                index = (tiledata[x // 2] >> ((x % 2) << 2)) & 0x0f
                singletile.append(index)
            tiles.append(singletile)
        if common.debug:
            print(" Loaded " + str(len(tiles)) + " tiles")
        # Draw the image
        tileheight = tilewidth = 8
        i = j = 0
        for map in maps:
            try:
                pal = map[0]
                xflip = map[1]
                yflip = map[2]
                tile = tiles[map[3]]
                for i2 in range(tileheight):
                    for j2 in range(tilewidth):
                        pixels[j + j2, i + i2] = palettes[pal][tile[i2 * tilewidth + j2]]
                # Very inefficient way to flip pixels
                if xflip or yflip:
                    sub = img.crop(box=(j, i, j + tilewidth, i + tileheight))
                    if yflip:
                        sub = ImageOps.flip(sub)
                    if xflip:
                        sub = ImageOps.mirror(sub)
                    img.paste(sub, box=(j, i))
            except (KeyError, IndexError):
                print("  [ERROR] Tile " + str(map[3]) + " not found")
            j += tilewidth
            if j >= width:
                j = 0
                i += tileheight
        # Draw palette
        if len(palettes) > 0:
            for i in range(len(palettes)):
                pixels = common.drawPalette(pixels, palettes[i], width, i * 10)
        img.save(outfolder + file.replace(".KPC", ".png"), "PNG")

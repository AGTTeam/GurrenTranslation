import os
import shutil
import common

infolder = "extract_NFP/NFP2D.NFP/"
outfolder = "work_KPC/"
if os.path.isdir(outfolder):
    shutil.rmtree(outfolder)
os.mkdir(outfolder)

print("Extracting KPC ...")
for file in os.listdir(infolder):
    if not file.endswith(".KPC"):
        continue
    print(" Processing", file, "...")
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
        f.seek(5, 1)
        bpp = 8 if common.readUShort(f) == 1 else 4
        f.seek(92)
        tilesize = common.readUInt(f)
        tileoffset = common.readUInt(f)
        f.seek(124)
        unk = common.readUInt(f)
        palsize = common.readUInt(f)
        paloffset = common.readUInt(f)
        if common.debug:
            print("  width:", width, "height:", height, "bpp:", bpp)
            print("  mapsize:", mapsize, "mapoffset:", mapoffset)
            print("  tilesize:", tilesize, "tileoffset:", tileoffset)
            print("  palsize:", palsize, "paloffset:", paloffset)
            print("  palcompressed:", palcompressed, "mapcompressed:", mapcompressed, "tilecompressed:", tilecompressed)
            print("  bits:", bits, "unk:", unk)
        # Read palette
        f.seek(paloffset)
        if palcompressed:
            paldata = common.decompress(f, palsize)
        else:
            paldata = f.read(palsize)
        # Read map data
        f.seek(mapoffset)
        if mapcompressed:
            mapdata = common.decompress(f, mapsize)
        else:
            mapdata = f.read(mapsize)
        # Read tile data
        f.seek(tileoffset)
        if tilecompressed:
            tiledata = common.decompress(f, tilesize)
        else:
            tiledata = f.read(tilesize)
        # Draw the image
        img = common.drawMappedImage(width, height, mapdata, tiledata, paldata, 8, bpp)
        img.save(outfolder + file.replace(".KPC", ".png"), "PNG")

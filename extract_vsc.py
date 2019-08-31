import os
import shutil
import common

infolder = "data/extract_NFP/NFP2D.NFP/"
outfolder = "data/out_VSC/"
if os.path.isdir(outfolder):
    shutil.rmtree(outfolder)
os.mkdir(outfolder)

print("Extracting VSC ...")
for file in os.listdir(infolder):
    if not file.endswith(".VSC"):
        continue
    print(" Processing", file, "...")
    with open(infolder + file, "rb") as f:
        # Read header
        f.seek(4)
        unk1 = common.readUShort(f)
        unk2 = common.readUShort(f)
        size = common.readUInt(f)
        unk3 = common.readUInt(f)
        bpp = 4 if common.readUInt(f) == 1 else 8
        width = common.readUInt(f)
        height = common.readUInt(f)
        unk4 = common.readUInt(f)
        mapsize = common.readUInt(f)
        unk5 = common.readUInt(f)
        tilesize = common.readUInt(f)
        if common.debug:
            print("  size:", size, "width:", width, "height:", height, "mapsize:", mapsize, "tilesize:", tilesize, "bpp:", bpp)
            print("  unk1:", unk1, "unk2:", unk2, "unk3:", unk3, "unk4:", unk4, "unk5:", unk5)
        # Read data
        if common.debug:
            print("  mapoffset:", f.tell())
        mapdata = f.read(mapsize)
        if common.debug:
            print("  tileoffset:", f.tell())
        tiledata = f.read(tilesize)
        if common.debug:
            print("  paloffset:", f.tell())
        cpal = common.readString(f, 4)
        if cpal != "CPAL":
            print("  [ERROR] Palette header", cpal)
        f.seek(20, 1)
        palnum = common.readUShort(f)
        f.seek(4, 1)
        paldata = f.read(palnum * 32)
        # Draw the image
        img = common.drawMappedImage(width, height, mapdata, tiledata, paldata, 8, bpp)
        img.save(outfolder + file.replace(".VSC", ".png"), "PNG")

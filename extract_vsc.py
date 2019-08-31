import os
import shutil
import common
import common_game as game

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
    with common.Stream(infolder + file, "rb") as f:
        # Read header
        f.seek(4)
        unk1 = f.readUShort()
        unk2 = f.readUShort()
        size = f.readUInt()
        unk3 = f.readUInt()
        bpp = 4 if f.readUInt() == 1 else 8
        width = f.readUInt()
        height = f.readUInt()
        unk4 = f.readUInt()
        mapsize = f.readUInt()
        unk5 = f.readUInt()
        tilesize = f.readUInt()
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
        cpal = f.readString(4)
        if cpal != "CPAL":
            print("  [ERROR] Palette header", cpal)
        f.seek(20, 1)
        palnum = f.readUShort()
        f.seek(4, 1)
        paldata = f.read(palnum * 32)
        # Draw the image
        img = game.drawMappedImage(width, height, mapdata, tiledata, paldata, 8, bpp)
        img.save(outfolder + file.replace(".VSC", ".png"), "PNG")

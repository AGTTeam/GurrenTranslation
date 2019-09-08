import game
from hacktools import common


def run():
    infolder = "data/extract_NFP/NFP2D.NFP/"
    outfolder = "data/out_VSC/"
    common.makeFolder(outfolder)

    common.logMessage("Extracting VSC to", outfolder, "...")
    files = common.getFiles(infolder, ".VSC")
    for file in common.showProgress(files):
        common.logDebug("Processing", file, "...")
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
            common.logDebug("size:", size, "width:", width, "height:", height, "mapsize:", mapsize, "tilesize:", tilesize, "bpp:", bpp)
            common.logDebug("unk1:", unk1, "unk2:", unk2, "unk3:", unk3, "unk4:", unk4, "unk5:", unk5)
            # Read data
            common.logDebug("mapoffset:", f.tell())
            mapdata = f.read(mapsize)
            common.logDebug("tileoffset:", f.tell())
            tiledata = f.read(tilesize)
            common.logDebug("paloffset:", f.tell())
            cpal = f.readString(4)
            if cpal != "CPAL":
                common.logError("Palette header", cpal)
                continue
            f.seek(20, 1)
            palnum = f.readUShort()
            f.seek(4, 1)
            paldata = f.read(palnum * 32)
            # Draw the image
            img = game.drawMappedImage(width, height, mapdata, tiledata, paldata, 8, bpp)
            img.save(outfolder + file.replace(".VSC", ".png"), "PNG")
    common.logMessage("Done! Extracted", len(files), "files")

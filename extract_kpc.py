import game
from hacktools import common, nds


def run():
    infolder = "data/extract_NFP/NFP2D.NFP/"
    outfolder = "data/out_KPC/"
    common.makeFolder(outfolder)

    common.logMessage("Extracting KPC to", outfolder, "...")
    files = common.getFiles(infolder, ".KPC")
    for file in common.showProgress(files):
        common.logDebug("Processing", file, "...")
        with common.Stream(infolder + file, "rb") as f:
            # Read header
            f.seek(4)
            bits = []
            for i in range(5):
                bits.append(f.readByte())
            palcompressed = f.readByte() == 1
            mapcompressed = f.readByte() == 1
            tilecompressed = f.readByte() == 1
            width = f.readUShort() * 8
            height = f.readUShort() * 8
            mapsize = f.readUInt()
            mapoffset = f.readUInt()
            f.seek(5, 1)
            bpp = 8 if f.readUShort() == 1 else 4
            f.seek(92)
            tilesize = f.readUInt()
            tileoffset = f.readUInt()
            f.seek(124)
            unk = f.readUInt()
            palsize = f.readUInt()
            paloffset = f.readUInt()
            common.logDebug("width:", width, "height:", height, "bpp:", bpp)
            common.logDebug("mapsize:", mapsize, "mapoffset:", mapoffset)
            common.logDebug("tilesize:", tilesize, "tileoffset:", tileoffset)
            common.logDebug("palsize:", palsize, "paloffset:", paloffset)
            common.logDebug("palcompressed:", palcompressed, "mapcompressed:", mapcompressed, "tilecompressed:", tilecompressed)
            common.logDebug("bits:", bits, "unk:", unk)
            # Read palette
            f.seek(paloffset)
            if palcompressed:
                paldata = nds.decompress(f, palsize)
            else:
                paldata = f.read(palsize)
            # Read map data
            f.seek(mapoffset)
            if mapcompressed:
                mapdata = nds.decompress(f, mapsize)
            else:
                mapdata = f.read(mapsize)
            # Read tile data
            f.seek(tileoffset)
            if tilecompressed:
                tiledata = nds.decompress(f, tilesize)
            else:
                tiledata = f.read(tilesize)
            # Draw the image
            img = game.drawMappedImage(width, height, mapdata, tiledata, paldata, 8, bpp)
            img.save(outfolder + file.replace(".KPC", ".png"), "PNG")
    common.logMessage("Done! Extracted", len(files), "files")

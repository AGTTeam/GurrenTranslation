import base64
import os
import pickle
import struct
from PIL import Image
from hacktools import common


def run():
    infolder = "data/extract_NFP/NFP2D.NFP/"
    workfolder = "data/work_YCE/"
    outfolder = "data/work_NFP/NFP2D.NFP/"
    infile = "data/yce_data.txt"
    if not os.path.isfile(infile):
        common.logError("Input file", infile, "not found.")
        return

    sections = {}
    with open(infile, "r") as yce:
        sections = common.getSection(yce, "")

    common.logMessage("Repacking YCE from", workfolder, "...")
    files = common.getFiles(infolder, ".YCE")
    for file in common.showProgress(files):
        filepath = infolder + file
        if os.path.isfile(workfolder + file):
            filepath = workfolder + file
        common.copyFile(filepath, outfolder + file)
        if file not in sections:
            continue
        pngname = file.replace(".YCE", ".png")
        if not os.path.isfile(workfolder + pngname):
            continue
        common.logDebug("Processing", file, "...")
        imgin = Image.open(workfolder + pngname)
        imgin = imgin.convert("RGBA")
        pixels = imgin.load()
        images = pickle.loads(base64.standard_b64decode(sections[file][0]))
        currheight = 0
        with common.Stream(outfolder + file, "r+b") as f:
            for img in images:
                # Read palette
                palette = []
                f.seek(img.paloffset)
                paldata = f.read(32)
                for i in range(0, 32, 2):
                    p = struct.unpack("<H", paldata[i:i+2])[0]
                    palette.append(common.readPalette(p))
                # Write new texture data
                for oam in img.oams:
                    f.seek(img.offset + img.oamsize + oam.offset * 32)
                    for i in range(oam.height // 8):
                        for j in range(oam.width // 8):
                            for i2 in range(8):
                                for j2 in range(0, 8, 2):
                                    index2 = common.getPaletteIndex(palette, pixels[oam.x + j * 8 + j2, currheight + oam.y + i * 8 + i2])
                                    index1 = common.getPaletteIndex(palette, pixels[oam.x + j * 8 + j2 + 1, currheight + oam.y + i * 8 + i2])
                                    f.writeByte(((index1) << 4) | index2)
                currheight += max(img.height, 10)
    common.logMessage("Done!")

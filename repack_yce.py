import base64
import os
import pickle
import struct
from PIL import Image
import common

ycein = "data/extract_NFP/NFP2D.NFP/"
ycework = "data/work_YCE/"
yceout = "data/work_NFP/NFP2D.NFP/"
ycefile = "data/yce_data.txt"

sections = {}
with open(ycefile, "r") as yce:
    sections = common.getSection(yce, "")

print("Repacking YCE ...")
for file in os.listdir(ycein):
    if not file.endswith(".YCE"):
        continue
    common.copyFile(ycein + file, yceout + file)
    if file not in sections:
        continue
    pngname = file.replace(".YCE", ".png")
    if not os.path.isfile(ycework + pngname):
        continue
    if common.debug:
        print(" Repacking", file, "...")
    imgin = Image.open(ycework + pngname)
    imgin = imgin.convert("RGBA")
    pixels = imgin.load()
    images = pickle.loads(base64.standard_b64decode(sections[file][0]))
    currheight = 0
    with common.Stream(yceout + file, "r+b") as f:
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

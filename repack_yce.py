import shutil
import os
import common
import base64
import pickle
import struct
from PIL import Image

ycein = "extract_NFP/NFP2D.NFP/"
ycework = "work_YCE/"
yceout = "work_NFP/NFP2D.NFP/"
ycefile = "yce_data.txt"

print("Repacking YCE ...")

sections = {}
with open(ycefile, "r") as yce:
    sections = common.getSection(yce, "")

for file in os.listdir(ycein):
    if not file.endswith(".YCE"):
        continue
    shutil.copyfile(ycein + file, yceout + file)
    if file not in sections == 0:
        continue
    pngname = file.replace(".YCE", ".png")
    if not os.path.isfile(ycework + pngname):
        continue
    if common.debug:
        print(" Repacking " + pngname + " ...")
    imgin = Image.open(ycework + pngname)
    imgin = imgin.convert("RGBA")
    pixels = imgin.load()
    images = pickle.loads(base64.standard_b64decode(sections[file]))
    currheight = 0
    with open(yceout + file, "r+b") as f:
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
                                common.writeByte(f, ((index1) << 4) | index2)
            currheight += max(img.height, 10)

import os
import shutil
import common
import struct
import base64
import pickle
from PIL import Image

infolder = "extract_NFP/NFP2D.NFP/"
outfolder = "work_YCE/"
outfile = "yce_data.txt"
if os.path.isdir(outfolder):
    shutil.rmtree(outfolder)
os.mkdir(outfolder)

print("Extracting YCE...")
with open(outfile, "w") as yce:
    for file in os.listdir(infolder):
        if not file.endswith(".YCE"):
            continue
        print("Processing", file, "...")
        with open(infolder + file, "rb") as f:
            # Read header
            f.seek(8)
            size = common.readUInt(f)  # size - header (7)
            f.seek(4, 1)  # Always 0
            f.seek(4, 1)  # Always 24
            animoffset = common.readUInt(f)  # Animation data offset
            unk = common.readUInt(f)  # ?
            num = common.readUInt(f)  # Number of images
            images = []
            for i in range(num):
                img = common.YCETexture()
                img.offset = common.readUInt(f) + 24  # Image data offset
                images.append(img)
            for img in images:
                if common.debug:
                    print(" Reading image at offset", img.offset, "...")
                f.seek(img.offset)
                img.size = common.readUInt(f)  # Image data size
                constant = common.readUInt(f)  # 0x1C
                if constant != 0x1C and common.debug:
                    print("  Constant is not 0x1C!", common.toHex(constant))
                img.oamnum = common.readUInt(f)  # Number of OAMs
                img.oamsize = common.readUInt(f)  # OAM data size
                img.tilesize = common.readUInt(f)  # Tile data size
                img.paloffset = common.readUInt(f) + img.offset  # Palette data offset (relative to offset)
                constant = common.readUInt(f)  # 0x01
                if constant != 0x01 and common.debug:
                    print("  Constant 2 is not 0x01!", common.toHex(constant))
                if common.debug:
                    print("  size:", img.size, "oamnum:", img.oamnum, "oamsize:", img.oamsize)
                    print("  tilesize:", img.tilesize, "paloffset:", img.paloffset)
                img.oams = []
                for j in range(img.oamnum):
                    oam = common.OAM()
                    oam.x = common.readShort(f)  # X position of the cell (-128 to 127)
                    oam.y = common.readShort(f)  # Y position of the cell (-256 to 255)
                    for x in range(8):
                        unkbyte = common.readByte(f)
                        if unkbyte != 0x00 and common.debug:
                            print("  unkbyte", x, "is not 0x00!", common.toHex(unkbyte))
                    shape = common.readByte(f)  # NCER OBJ Shape
                    size = common.readByte(f)  # NCER OBJ Size
                    for x in range(2):
                        unkbyte = common.readByte(f)
                        if unkbyte != 0x00 and common.debug:
                            print("  unkbyte2", x, "is not 0x00!", common.toHex(unkbyte))
                    oam.offset = common.readUInt(f)
                    # Table from http://www.romhacking.net/documents/%5B469%5Dnds_formats.htm#NCER
                    if shape == 0:
                        if size == 0:
                            tilesize = (8, 8)
                        elif size == 1:
                            tilesize = (16, 16)
                        elif size == 2:
                            tilesize = (32, 32)
                        elif size == 3:
                            tilesize = (64, 64)
                    elif shape == 1:
                        if size == 0:
                            tilesize = (16, 8)
                        elif size == 1:
                            tilesize = (32, 8)
                        elif size == 2:
                            tilesize = (32, 16)
                        elif size == 3:
                            tilesize = (64, 32)
                    elif shape == 2:
                        if size == 0:
                            tilesize = (8, 16)
                        elif size == 1:
                            tilesize = (8, 32)
                        elif size == 2:
                            tilesize = (16, 32)
                        elif size == 3:
                            tilesize = (32, 64)
                    oam.width = tilesize[0]
                    oam.height = tilesize[1]
                    img.oams.append(oam)
                # Calculate width and height
                minx = miny = 512
                maxx = maxy = -512
                for oam in img.oams:
                    minx = min(minx, oam.x)
                    miny = min(miny, oam.y)
                    maxx = max(maxx, oam.x + oam.width)
                    maxy = max(maxy, oam.y + oam.height)
                img.width = maxx - minx
                img.height = maxy - miny
                for oam in img.oams:
                    oam.x -= minx
                    oam.y -= miny
                if common.debug:
                    print("  width:", img.width, "height:", img.height)
                    print("  oams:", img.oams)
            # Create image
            width = height = 0
            for img in images:
                width = max(width, img.width + 40)
                height += max(img.height, 10)
            outimg = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            pixels = outimg.load()
            # Read images
            currheight = 0
            for img in images:
                # Load palette
                palette = []
                f.seek(img.paloffset)
                paldata = f.read(32)
                for i in range(0, 32, 2):
                    p = struct.unpack("<H", paldata[i:i+2])[0]
                    palette.append(common.readPalette(p))
                # Read tile data
                f.seek(img.offset + img.oamsize)
                tiledata = f.read(img.tilesize)
                for oam in img.oams:
                    x = oam.offset * 64
                    for i in range(oam.height // 8):
                        for j in range(oam.width // 8):
                            for i2 in range(8):
                                for j2 in range(8):
                                    index = (tiledata[x // 2] >> ((x % 2) << 2)) & 0x0f
                                    pixels[oam.x + j * 8 + j2, currheight + oam.y + i * 8 + i2] = palette[index]
                                    x += 1
                # Draw palette
                pixels = common.drawPalette(pixels, palette, width - 40, currheight)
                currheight += max(img.height, 10)
            outimg.save(outfolder + file.replace(".YCE", ".png"), "PNG")
        yce.write(file + "=" + base64.standard_b64encode(pickle.dumps(images)).decode() + "\n")

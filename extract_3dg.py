import os
import shutil
import common
from PIL import Image

infolder = "extract_NFP/NFP3D.NFP/"
outfolder = "work_3DG/"
outfile = "3dg_data.txt"
if os.path.isdir(outfolder):
    shutil.rmtree(outfolder)
os.mkdir(outfolder)

bpp = [0, 8, 2, 4, 8, 2, 8, 16]


class Texture:
    name = ""
    offset = 0
    format = 0
    width = 0
    height = 0
    size = 0


class Palette:
    name = ""
    offset = 0
    size = 0
    data = []


with open(outfile, "w") as dg:
    for file in os.listdir(infolder):
        if not file.endswith(".3DG"):
            continue
        print("Processing " + file + " ...")
        first = True
        with open(infolder + file, "rb") as f:
            # Skip the 3DKT header
            f.seek(8)
            nsbmdstart = common.readUShort(f)
            # Read the TEX0 offset
            f.seek(nsbmdstart + 20)
            texstart = common.readUShort(f)
            if texstart == 17485:  # MDL0
                continue
            blockoffset = nsbmdstart + texstart
            # Read TEX0 block
            f.seek(blockoffset + 4)
            blocksize = common.readUInt(f)
            blocklimit = blocksize + blockoffset
            f.seek(4, 1)
            texdatasize = common.readUShort(f) * 8
            f.seek(6, 1)
            texdataoffset = common.readUInt(f) + blockoffset
            f.seek(4, 1)
            sptexsize = common.readUShort(f) * 8
            f.seek(6, 1)
            sptexoffset = common.readUInt(f) + blockoffset
            spdataoffset = common.readUInt(f) + blockoffset
            f.seek(4, 1)
            paldatasize = common.readUShort(f) * 8
            f.seek(2, 1)
            paldefoffset = common.readUInt(f) + blockoffset
            paldataoffset = common.readUInt(f) + blockoffset
            if common.debug:
                print(" blocksize: " + str(blocksize) + " blocklimit: " + str(blocklimit))
                print(" texdataoffset: " + str(texdataoffset) + " texdatasize: " + str(texdatasize))
                print(" sptexoffset: " + str(sptexoffset) + " sptexsize: " + str(sptexsize) + " texdataoffset: " + str(texdataoffset))
                print(" paldataoffset: " + str(paldataoffset) + " paldatasize: " + str(paldatasize) + " paldefoffset: " + str(paldefoffset))
            # Texture definition
            f.seek(1, 1)
            texnum = common.readByte(f)
            pos = f.tell()
            f.seek(paldefoffset + 1)
            palnum = common.readByte(f)
            f.seek(pos)
            if common.debug:
                print(" texnum: " + str(texnum) + " palnum: " + str(palnum))
            f.seek(14 + (texnum * 4), 1)
            textures = []
            palettes = []
            for i in range(texnum):
                offset = common.readUShort(f) * 8
                param = common.readUShort(f)
                f.seek(4, 1)
                tex = Texture()
                tex.format = (param >> 10) & 7
                tex.width = 8 << ((param >> 4) & 7)
                tex.height = 8 << ((param >> 7) & 7)
                tex.size = tex.width * tex.height * bpp[tex.format] // 8
                if tex.format == 5:
                    tex.offset = offset + sptexoffset
                else:
                    tex.offset = offset + texdataoffset
                textures.append(tex)
            # Texture name
            for tex in textures:
                tex.name = common.readString(f, 16)
                if common.debug:
                    print(" Texture " + tex.name + " format: " + str(tex.format) + " width: " + str(tex.width) + " height: " + str(tex.height) + " size: " + str(tex.size) + " offset: " + str(tex.offset))
            # Palette definition
            f.seek(paldefoffset + 2 + 14 + (palnum * 4))
            for i in range(palnum):
                pal = Palette()
                pal.offset = (common.readUShort(f) * 8) + paldataoffset
                f.seek(2, 1)
                palettes.append(pal)
            # Palette size
            if palnum > 0:
                for i in range(palnum):
                    r = i + 1
                    while r < len(palettes) and palettes[r].offset == palettes[i].offset:
                        r += 1
                    if r != palnum:
                        palettes[i].size = palettes[r].offset - palettes[i].offset
                    else:
                        palettes[i].size = blocklimit - palettes[i].offset
                palettes[i].size = blocklimit - palettes[i].offset
            # Palette name
            for pal in palettes:
                pal.name = common.readString(f, 16)
                if common.debug:
                    print(" Palette " + pal.name + " size: " + str(pal.size) + " offset: " + str(pal.offset))
            # Traverse palette
            for pal in palettes:
                f.seek(pal.offset)
                pal.data = []
                for i in range(pal.size // 2):
                    pal.data.append(common.readPalette(common.readShort(f)))
                # if common.debug:
                #    print(pal.data)
            # Traverse texture
            for texi in range(len(textures)):
                tex = textures[texi]
                if tex.format == 5:
                    continue
                print("  Exporting " + tex.name + " ...")
                palette = None
                if tex.format != 7:
                    palette = palettes[texi]
                # Write data
                if first:
                    first = False
                    dg.write("!FILE:" + file + "\n")
                if tex.format != 7:
                    texdata = (tex.format, tex.width, tex.height, tex.size, tex.offset, palette.name, palette.size, palette.offset)
                else:
                    texdata = (tex.format, tex.width, tex.height, tex.size, tex.offset)
                dg.write(tex.name + "=" + ",".join(str(item) for item in texdata) + "\n")
                # Export texture
                f.seek(tex.offset)
                data = f.read(tex.size)
                if tex.format != 7:
                    palette = palette.data
                    img = Image.new("RGBA", (tex.width + 40, max(tex.height, (len(palette) // 8) * 5)), (0, 0, 0, 0))
                else:
                    img = Image.new("RGBA", (tex.width, tex.height), (0, 0, 0, 0))
                pixels = img.load()
                # A3I5 Translucent Texture (3bit Alpha, 5bit Color Index)
                if tex.format == 1:
                    for i in range(tex.height):
                        for j in range(tex.width):
                            x = i * tex.width + j
                            index = data[x] & 0x1f
                            alpha = (data[x] >> 5) & 7
                            alpha = ((alpha * 4) + (alpha // 2)) << 3
                            if index < len(palette):
                                pixels[j, i] = (palette[index][0], palette[index][1], palette[index][2], alpha)
                            elif common.warning:
                                print("  [WARNING] Index " + str(index) + " is out of range " + str(len(palette)))
                # 4-color Palette
                elif tex.format == 2:
                    for i in range(tex.height):
                        for j in range(tex.width):
                            x = i * tex.width + j
                            index = (data[x // 4] >> ((x % 4) << 1)) & 3
                            if index < len(palette):
                                pixels[j, i] = palette[index]
                            elif common.warning:
                                print("  [WARNING] Index " + str(index) + " is out of range " + str(len(palette)))
                # 16-color Palette
                elif tex.format == 3:
                    for i in range(tex.height):
                        for j in range(tex.width):
                            x = i * tex.width + j
                            index = (data[x // 2] >> ((x % 2) << 2)) & 0x0f
                            if index < len(palette):
                                pixels[j, i] = palette[index]
                            elif common.warning:
                                print("  [WARNING] Index " + str(index) + " is out of range " + str(len(palette)))
                # 256-color Palette
                elif tex.format == 4:
                    for i in range(tex.height):
                        for j in range(tex.width):
                            x = i * tex.width + j
                            index = data[x]
                            if index < len(palette):
                                pixels[j, i] = palette[index]
                            elif common.warning:
                                print("  [WARNING] Index " + str(index) + " is out of range " + str(len(palette)))
                # A5I3 Translucent Texture (5bit Alpha, 3bit Color Index)
                elif tex.format == 6:
                    for i in range(tex.height):
                        for j in range(tex.width):
                            x = i * tex.width + j
                            index = data[x] & 0x7
                            alpha = (data[x] >> 3) & 0x1f
                            alpha = ((alpha * 4) + (alpha // 2)) << 3
                            if index < len(palette):
                                pixels[j, i] = (palette[index][0], palette[index][1], palette[index][2], alpha)
                            elif common.warning:
                                print("  [WARNING] Index " + str(index) + " is out of range " + str(len(palette)))
                # Direct Color Texture
                elif tex.format == 7:
                    for i in range(tex.height):
                        for j in range(tex.width):
                            x = i * tex.width + j
                            p = data[x * 2] + (data[x * 2 + 1] << 8)
                            pixels[j, i] = (((p >> 0) & 0x1f) << 3, ((p >> 5) & 0x1f) << 3, ((p >> 10) & 0x1f) << 3, 0xff if (p & 0x8000) else 0)
                # Draw palette
                if tex.format != 7:
                    pixels = common.drawPalette(pixels, palette, tex.width)
                img.save(outfolder + file.replace(".3DG", "") + "_" + tex.name + ".png", "PNG")

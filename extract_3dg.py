import os
import shutil
from PIL import Image
import common

infolder = "data/extract_NFP/NFP3D.NFP/"
outfolder = "data/out_3DG/"
outfile = "data/3dg_data.txt"
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


# Code based on nsbmd tool
print("Extracting 3DG ...")
with open(outfile, "w") as dg:
    for file in os.listdir(infolder):
        if not file.endswith(".3DG"):
            continue
        print(" Processing", file, "...")
        first = True
        with common.Stream(infolder + file, "rb") as f:
            # Skip the 3DKT header
            f.seek(8)
            nsbmdstart = f.readUShort()
            # Read the TEX0 offset
            f.seek(nsbmdstart + 20)
            texstart = f.readUShort()
            # If texstart points to MDL0, the model doesn't have any texture
            if texstart == 17485:  # MDL0
                continue
            blockoffset = nsbmdstart + texstart
            # Read TEX0 block
            f.seek(blockoffset + 4)
            blocksize = f.readUInt()
            blocklimit = blocksize + blockoffset
            f.seek(4, 1)
            texdatasize = f.readUShort() * 8
            f.seek(6, 1)
            texdataoffset = f.readUInt() + blockoffset
            f.seek(4, 1)
            sptexsize = f.readUShort() * 8
            f.seek(6, 1)
            sptexoffset = f.readUInt() + blockoffset
            spdataoffset = f.readUInt() + blockoffset
            f.seek(4, 1)
            paldatasize = f.readUShort() * 8
            f.seek(2, 1)
            paldefoffset = f.readUInt() + blockoffset
            paldataoffset = f.readUInt() + blockoffset
            if common.debug:
                print("  blocksize:", blocksize, "blocklimit:", blocklimit)
                print("  texdataoffset:", texdataoffset, "texdatasize:", texdatasize)
                print("  sptexoffset:", sptexoffset, "sptexsize:", sptexsize, "spdataoffset:", spdataoffset)
                print("  paldataoffset:", paldataoffset, "paldatasize:", paldatasize, "paldefoffset:", paldefoffset)
            # Texture definition
            f.seek(1, 1)
            texnum = f.readByte()
            pos = f.tell()
            f.seek(paldefoffset + 1)
            palnum = f.readByte()
            f.seek(pos)
            if common.debug:
                print("  texnum:", texnum, "palnum:", palnum)
            f.seek(14 + (texnum * 4), 1)
            textures = []
            palettes = []
            for i in range(texnum):
                offset = f.readUShort() * 8
                param = f.readUShort()
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
                tex.name = f.readString(16)
                if common.debug:
                    print("  Texture", tex.name, "format:", tex.format, "width:", tex.width, "height:", tex.height, "size:", tex.size, "offset:", tex.offset)
            # Palette definition
            f.seek(paldefoffset + 2 + 14 + (palnum * 4))
            for i in range(palnum):
                pal = Palette()
                pal.offset = (f.readUShort() * 8) + paldataoffset
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
                pal.name = f.readString(16)
                if common.debug:
                    print("  Palette", pal.name, "size:", pal.size, "offset:", pal.offset)
            # Traverse palette
            for pal in palettes:
                f.seek(pal.offset)
                pal.data = []
                for i in range(pal.size // 2):
                    pal.data.append(common.readPalette(f.readShort()))
            # Traverse texture
            for texi in range(len(textures)):
                tex = textures[texi]
                print("   Exporting", tex.name, "...")
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
                if tex.format == 5:
                    r = tex.size >> 1
                    f.seek(spdataoffset)
                    spdata = []
                    for i in range(r // 2):
                        spdata.append(f.readUShort())
                    spdataoffset += r
                # Export texture
                f.seek(tex.offset)
                if tex.format == 5:
                    data = []
                    for i in range(tex.size // 4):
                        data.append(f.readUInt())
                else:
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
                                print("   [WARNING] Index", index, "is out of range", len(palette))
                # 4-color Palette
                elif tex.format == 2:
                    for i in range(tex.height):
                        for j in range(tex.width):
                            x = i * tex.width + j
                            index = (data[x // 4] >> ((x % 4) << 1)) & 3
                            if index < len(palette):
                                pixels[j, i] = palette[index]
                            elif common.warning:
                                print("   [WARNING] Index", index, "is out of range", len(palette))
                # 16-color Palette
                elif tex.format == 3:
                    for i in range(tex.height):
                        for j in range(tex.width):
                            x = i * tex.width + j
                            index = (data[x // 2] >> ((x % 2) << 2)) & 0x0f
                            if index < len(palette):
                                pixels[j, i] = palette[index]
                            elif common.warning:
                                print("   [WARNING] Index", index, "is out of range", len(palette))
                # 256-color Palette
                elif tex.format == 4:
                    for i in range(tex.height):
                        for j in range(tex.width):
                            x = i * tex.width + j
                            index = data[x]
                            if index < len(palette):
                                pixels[j, i] = palette[index]
                            elif common.warning:
                                print("  [WARNING] Index", index, "is out of range", len(palette))
                # 4x4-Texel Compressed Texture [TODO]
                elif tex.format == 5:
                    w = tex.width // 4
                    h = tex.height // 4
                    for y in range(h):
                        for x in range(w):
                            index = y * w + x
                            t = data[index]
                            d = spdata[index]
                            addr = d & 0x3fff
                            pali = addr << 1
                            mode = (d >> 14) & 3
                            for r in range(4):
                                for c in range(4):
                                    texel = (t >> ((r * 4 + c) * 2)) & 3
                                    i = y * 4 + r
                                    j = x * 4 + c
                                    try:
                                        if mode == 0:
                                            if texel == 3:
                                                pixels[j, i] = (0xff, 0xff, 0xff, 0)
                                            else:
                                                pixels[j, i] = palette[pali + texel]
                                        elif mode == 2:
                                            pixels[j, i] = palette[pali + texel]
                                        elif mode == 1:
                                            if texel == 0 or texel == 1:
                                                pixels[j, i] = palette[pali + texel]
                                            elif texel == 2:
                                                pixels[j, i] = common.sumColors(palette[pali], palette[pali + 1])
                                            elif texel == 3:
                                                pixels[j, i] = (0xff, 0xff, 0xff, 0)
                                        elif mode == 3:
                                            if texel == 0 or texel == 1:
                                                pixels[j, i] = palette[pali + texel]
                                            elif texel == 2:
                                                pixels[j, i] = common.sumColors(palette[pali], palette[pali + 1], 5, 3, 8)
                                            elif texel == 3:
                                                pixels[j, i] = common.sumColors(palette[pali], palette[pali + 1], 3, 5, 8)
                                    except IndexError:
                                        pixels[j, i] = (0x00, 0x00, 0x00, 0xff)
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
                                print("   [WARNING] Index", index, "is out of range", len(palette))
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

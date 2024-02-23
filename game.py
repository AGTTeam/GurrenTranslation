import os
import struct
from PIL import Image, ImageOps
from hacktools import common, nitro

# Control codes found in strings
codes = [0x09, 0x0A, 0x20, 0xA5]
# Control codes and random ASCII characters found in BIN strings
bincodes = [0x09, 0x0A, 0x20, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x42, 0x43, 0x64, 0xA5]
# Identifier and size of SPC code blocks
spccodes = {
    0x28: 1, 0x2A: 1, 0x54: 1, 0x58: 1, 0x59: 1, 0x5A: 1, 0x5B: 1, 0x5C: 1, 0x5D: 1, 0x8F: 1,
    0x20: 2, 0x50: 2, 0x52: 2, 0x72: 2, 0x73: 2, 0x79: 2,
    0x11: 4, 0x29: 4, 0x80: 4, 0x81: 4, 0x32: 4, 0x3A: 4,
    0x12: 5, 0x21: 5, 0x31: 5, 0x33: 5, 0x37: 5, 0x39: 5
}
# Characters to replace in sections
fixchars = [("’", "'"), ("‘", "'"), ("…", "..."), ("—", "-"), ("～", "~"), ("	", " ")]


# Game-specific strings
def readShiftJIS(f):
    len = f.readShort()
    pos = f.tell()
    # Check if the string is all ascii
    ascii = True
    for i in range(len - 1):
        byte = f.readByte()
        if byte != 0x0A and (byte < 32 or byte > 122):
            ascii = False
            break
    if not ascii:
        f.seek(pos)
        sjis = ""
        i = 0
        while i < len - 1:
            byte = f.readByte()
            if byte in codes:
                sjis += "<" + common.toHex(byte, True) + ">"
                i += 1
            else:
                f.seek(-1, 1)
                try:
                    sjis += f.read(2).decode("shift-jis").replace("〜", "～")
                except UnicodeDecodeError:
                    common.logError("UnicodeDecodeError")
                    sjis += "|"
                i += 2
        return sjis
    return ""


def writeShiftJIS(f, str, writelen=True, maxlen=0):
    if str == "":
        if writelen:
            f.writeShort(1)
        f.writeByte(0)
        return 1
    i = 0
    strlen = 0
    if writelen:
        lenpos = f.tell()
        f.writeShort(strlen)
    if ord(str[0]) < 256 or str[0] == "“" or str[0] == "”" or str[0] == "↓":
        # ASCII string
        while i < len(str):
            # Add a space if the next character is <XX>, UNK(XXXX) or CUS(XXXX)
            if i < len(str) - 1 and str[i+1] == "<":
                str = str[:i+1] + " " + str[i+1:]
            elif i < len(str) - 4 and (str[i+1:i+5] == "UNK(" or str[i+1:i+5] == "CUS("):
                str = str[:i+1] + " " + str[i+1:]
            char = str[i]
            # Code format <XX>
            if char == "<" and i < len(str) - 3 and str[i+3] == ">":
                try:
                    if maxlen > 0 and strlen + 1 > maxlen:
                        return -1
                    code = str[i+1] + str[i+2]
                    f.write(bytes.fromhex(code))
                    strlen += 1
                except ValueError:
                    common.logwarning("Invalid escape code", str[i+1], str[i+2])
                i += 4
            # Unknown format UNK(XXXX)
            elif char == "U" and i < len(str) - 4 and str[i:i+4] == "UNK(":
                if maxlen > 0 and strlen + 2 > maxlen:
                    return -1
                code = str[i+4] + str[i+5]
                f.write(bytes.fromhex(code))
                code = str[i+6] + str[i+7]
                f.write(bytes.fromhex(code))
                i += 9
                strlen += 2
            # Custom full-size glyph CUS(XXXX)
            elif char == "C" and i < len(str) - 4 and str[i:i+4] == "CUS(":
                if maxlen > 0 and strlen + 2 > maxlen:
                    return -1
                f.write(bytes.fromhex(common.table[str[i+4:i+8]]))
                i += 9
                strlen += 2
            else:
                if i + 1 == len(str):
                    bigram = char + " "
                else:
                    bigram = char + str[i+1]
                i += 2
                if maxlen > 0 and strlen + 2 > maxlen:
                    return -1
                if bigram not in common.table:
                    try:
                        common.logWarning("Bigram not found:", bigram, "in string", str)
                    except UnicodeEncodeError:
                        common.logWarning("Bigram not found in string", str)
                    bigram = "  "
                f.write(bytes.fromhex(common.table[bigram]))
                strlen += 2
    else:
        # SJIS string
        str = str.replace("～", "〜")
        while i < len(str):
            char = str[i]
            if char == "<":
                code = str[i+1] + str[i+2]
                i += 4
                f.write(bytes.fromhex(code))
                strlen += 1
            else:
                i += 1
                f.write(char.encode("shift-jis"))
                strlen += 2
    if writelen:
        f.writeZero(1)
        pos = f.tell()
        f.seek(lenpos)
        f.writeShort(strlen + 1)
        f.seek(pos)
    return strlen + 1


def detectShiftJIS(f):
    ret = ""
    while True:
        b1 = f.readByte()
        if ret != "" and b1 == 0:
            return ret
        if ret != "" and b1 in bincodes:
            ret += "<" + common.toHex(b1, True) + ">"
            continue
        b2 = f.readByte()
        if common.checkShiftJIS(b1, b2):
            f.seek(-2, 1)
            try:
                ret += f.read(2).decode("cp932").replace("〜", "～")
            except UnicodeDecodeError:
                if ret.count("UNK(") >= 5:
                    return ""
                ret += "UNK(" + common.toHex(b1, True) + common.toHex(b2, True) + ")"
        elif len(ret) > 0 and ret.count("UNK(") < 5:
            ret += "UNK(" + common.toHex(b1, True) + common.toHex(b2, True) + ")"
        else:
            return ""


# Game-specific textures
class YCETexture:
    width = 0
    height = 0
    offset = 0
    size = 0
    oamnum = 0
    oamsize = 0
    tilesize = 0
    paloffset = 0
    oams = []


class OAM:
    x = 0
    y = 0
    width = 0
    height = 0
    offset = 0


def readPaletteData(paldata):
    palettes = []
    for j in range(len(paldata) // 32):
        palette = []
        for i in range(0, 32, 2):
            p = struct.unpack("<H", paldata[j * 32 + i:j * 32 + i + 2])[0]
            palette.append(common.readPalette(p))
        palettes.append(palette)
    common.logDebug("Loaded", len(palettes), "palettes")
    return palettes


def readMappedImage(imgfile, width, height, paldata, fixtransp=False, tilesize=8):
    palettes = readPaletteData(paldata)
    # Read the image
    img = Image.open(imgfile)
    img = img.convert("RGBA")
    pixels = img.load()
    # Split image into tiles and maps
    tiles = []
    maps = []
    i = j = 0
    while i < height:
        tilecolors = []
        for i2 in range(tilesize):
            for j2 in range(tilesize):
                tilecolors.append(pixels[j + j2, i + i2])
        pal = common.findBestPalette(palettes, tilecolors)
        tile = []
        for tilecolor in tilecolors:
            tile.append(getPaletteIndex(palettes[pal], tilecolor, fixtransp))
        # Search for a repeated tile
        found = -1
        for ti in range(len(tiles)):
            if tiles[ti] == tile:
                found = ti
                break
        if found != -1:
            maps.append((pal, 0, 0, found))
        else:
            tiles.append(tile)
            maps.append((pal, 0, 0, len(tiles) - 1))
        j += tilesize
        if j >= width:
            j = 0
            i += tilesize
    return tiles, maps


def drawMappedImage(width, height, mapdata, tiledata, paldata, tilesize=8, bpp=4):
    palnum = len(paldata) // 32
    img = Image.new("RGBA", (width + 40, max(height, palnum * 10)), (0, 0, 0, 0))
    pixels = img.load()
    # Maps
    maps = []
    for i in range(0, len(mapdata), 2):
        map = struct.unpack("<h", mapdata[i:i+2])[0]
        pal = (map >> 12) & 0xF
        xflip = (map >> 10) & 1
        yflip = (map >> 11) & 1
        tile = map & 0x3FF
        maps.append((pal, xflip, yflip, tile))
    common.logDebug("Loaded", len(maps), "maps")
    # Tiles
    tiles = []
    for i in range(len(tiledata) // (32 if bpp == 4 else 64)):
        singletile = []
        for j in range(tilesize * tilesize):
            x = i * (tilesize * tilesize) + j
            if bpp == 4:
                index = (tiledata[x // 2] >> ((x % 2) << 2)) & 0x0f
            else:
                index = tiledata[x]
            singletile.append(index)
        tiles.append(singletile)
    common.logDebug("Loaded", len(tiles), "tiles")
    # Palette
    palettes = readPaletteData(paldata)
    pals = []
    for palette in palettes:
        pals += palette
    # Draw the image
    i = j = 0
    for map in maps:
        try:
            pal = map[0]
            xflip = map[1]
            yflip = map[2]
            tile = tiles[map[3]]
            for i2 in range(tilesize):
                for j2 in range(tilesize):
                    pixels[j + j2, i + i2] = pals[16 * pal + tile[i2 * tilesize + j2]]
            # Very inefficient way to flip pixels
            if xflip or yflip:
                sub = img.crop(box=(j, i, j + tilesize, i + tilesize))
                if yflip:
                    sub = ImageOps.flip(sub)
                if xflip:
                    sub = ImageOps.mirror(sub)
                img.paste(sub, box=(j, i))
        except (KeyError, IndexError):
            common.logWarning("Tile or palette", str(map), "not found")
        j += tilesize
        if j >= width:
            j = 0
            i += tilesize
    # Draw palette
    if len(palettes) > 0:
        for i in range(len(palettes)):
            pixels = common.drawPalette(pixels, palettes[i], width, i * 10)
    return img


# This is a copy of common.getPaletteIndex to get the old behavior
def getPaletteIndex(palette, color, fixtransp=False, starti=0, palsize=-1, checkalpha=False, zerotransp=True):
    if color[3] == 0 and zerotransp:
        return 0
    if palsize == -1:
        palsize = len(palette)
    zeroalpha = -1
    for i in range(starti, starti + palsize):
        if fixtransp and i == starti:
            continue
        if palette[i][0] == color[0] and palette[i][1] == color[1] and palette[i][2] == color[2] and (not checkalpha or palette[i][3] == color[3]):
            return i - starti
        if palette[i][3] == 0:
            zeroalpha = i - starti
    if palette[starti][0] == color[0] and palette[starti][1] == color[1] and palette[starti][2] == color[2] and (not checkalpha or palette[starti][3] == color[3]):
        return 0
    if checkalpha and color[3] == 0 and zeroalpha != -1:
        return zeroalpha
    mindist = 0xFFFFFFFF
    disti = 0
    for i in range(starti + 1, starti + palsize):
        distance = common.getColorDistance(color, palette[i], checkalpha)
        if distance < mindist:
            mindist = distance
            disti = i - starti
    common.logDebug("Color", color, "not found, closest color:", palette[disti])
    return disti


# Same as above
def repackNSBMD(workfolder, infolder, outfolder, extension=".nsbmd", writefunc=None):
    common.logMessage("Repacking NSBMD from", workfolder, "...")
    files = common.getFiles(infolder, extension)
    for file in common.showProgress(files):
        common.logDebug("Processing", file, "...")
        common.copyFile(infolder + file, outfolder + file)
        nsbmd = nitro.readNSBMD(infolder + file)
        if nsbmd is not None and len(nsbmd.textures) > 0:
            fixtransp = False
            if writefunc is not None:
                fixtransp = writefunc(file, nsbmd)
            for texi in range(len(nsbmd.textures)):
                pngname = file.replace(extension, "") + "_" + nsbmd.textures[texi].name + ".png"
                if os.path.isfile(workfolder + pngname):
                    common.logDebug(" Repacking", pngname, "...")
                    writeNSBMD(outfolder + file, nsbmd, texi, workfolder + pngname, fixtransp)
    common.logMessage("Done!")


def writeNSBMD(file, nsbmd, texi, infile, fixtransp=False):
    img = Image.open(infile)
    img = img.convert("RGBA")
    pixels = img.load()
    tex = nsbmd.textures[texi]
    with common.Stream(file, "r+b") as f:
        # Read palette
        if tex.format != 7:
            palette = nsbmd.palettes[texi]
            paldata = palette.data
        # Write new texture data
        f.seek(tex.offset)
        # A3I5 Translucent Texture (3bit Alpha, 5bit Color Index)
        if tex.format == 1:
            for i in range(tex.height):
                for j in range(tex.width):
                    index = common.getPaletteIndex(paldata, pixels[j, i], fixtransp)
                    alpha = (pixels[j, i][3] * 8) // 256
                    f.writeByte(index | (alpha << 5))
        # 4-color Palette
        elif tex.format == 2:
            for i in range(tex.height):
                for j in range(0, tex.width, 4):
                    index1 = common.getPaletteIndex(paldata, pixels[j, i], fixtransp)
                    index2 = common.getPaletteIndex(paldata, pixels[j + 1, i], fixtransp)
                    index3 = common.getPaletteIndex(paldata, pixels[j + 2, i], fixtransp)
                    index4 = common.getPaletteIndex(paldata, pixels[j + 3, i], fixtransp)
                    f.writeByte((index4 << 6) | (index3 << 4) | (index2 << 2) | index1)
        # 16/256-color Palette
        elif tex.format == 3 or tex.format == 4:
            for i in range(tex.height):
                for j in range(0, tex.width, 2):
                    index1 = common.getPaletteIndex(paldata, pixels[j, i], fixtransp)
                    index2 = common.getPaletteIndex(paldata, pixels[j + 1, i], fixtransp)
                    nitro.writeNCGRData(f, 4 if tex.format == 3 else 8, index1, index2)
        # 4x4-Texel Compressed Texture
        elif tex.format == 5:
            common.logError("Texture format 5 not implemented")
        # A5I3 Translucent Texture (5bit Alpha, 3bit Color Index)
        elif tex.format == 6:
            for i in range(tex.height):
                for j in range(tex.width):
                    index = common.getPaletteIndex(paldata, pixels[j, i], fixtransp)
                    alpha = (pixels[j, i][3] * 32) // 256
                    f.writeByte(index | (alpha << 3))
        # Direct Color Texture
        elif tex.format == 7:
            common.logError("Texture format 7 not implemented")


def read3DG(file):
    return file.startswith("MSW_") or file.startswith("RSLT_")


def write3DG(file, nsbmd):
    fixtransp = file.startswith("MSW_")
    return fixtransp, False, False, False

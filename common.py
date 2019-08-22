import struct
import os
import math

debug = False
warning = True
codes = [0x09, 0x0A, 0x20, 0xA5]
bincodes = [0x09, 0x0A, 0x20, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x42, 0x43, 0x64, 0xA5]
spccodes = {
    0x28: 1, 0x2A: 1, 0x54: 1, 0x58: 1, 0x59: 1, 0x5A: 1, 0x5B: 1, 0x5C: 1, 0x5D: 1, 0x8F: 1,
    0x20: 2, 0x50: 2, 0x52: 2, 0x72: 2, 0x73: 2, 0x79: 2,
    0x11: 4, 0x29: 4, 0x80: 4, 0x81: 4, 0x3A: 4,
    0x12: 5, 0x21: 5, 0x31: 5, 0x33: 5
}
table = {}


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


def toHex(byte):
    hexstr = hex(byte)[2:].upper()
    if len(hexstr) == 1:
        return "0" + hexstr
    return hexstr


def readInt(f):
    return struct.unpack("<i", f.read(4))[0]


def readUInt(f):
    return struct.unpack("<I", f.read(4))[0]


def readShort(f):
    return struct.unpack("<h", f.read(2))[0]


def readUShort(f):
    return struct.unpack("<H", f.read(2))[0]


def readByte(f):
    return struct.unpack("B", f.read(1))[0]


def readPalette(p):
    return (((p >> 0) & 0x1f) << 3, ((p >> 5) & 0x1f) << 3, ((p >> 10) & 0x1f) << 3, 0xff)


def readString(f, length):
    str = ""
    for i in range(length):
        byte = readByte(f)
        # These control characters can be found in texture names, replace them with a space
        if byte == 0x82 or byte == 0x86:
            byte = 0x20
        if byte != 0:
            str += chr(byte)
    return str


def readNullString(f):
    str = ""
    while True:
        byte = readByte(f)
        if byte == 0:
            break
        else:
            str += chr(byte)
    return str


def readShiftJIS(f):
    len = readShort(f)
    pos = f.tell()
    # Check if the string is all ascii
    ascii = True
    for i in range(len - 1):
        byte = readByte(f)
        if byte != 0x0A and (byte < 32 or byte > 122):
            ascii = False
            break
    if not ascii:
        f.seek(pos)
        sjis = ""
        i = 0
        while i < len - 1:
            byte = readByte(f)
            if byte in codes:
                sjis += "<" + toHex(byte) + ">"
                i += 1
            else:
                f.seek(-1, 1)
                try:
                    sjis += f.read(2).decode("shift-jis").replace("〜", "～")
                except UnicodeDecodeError:
                    print("[ERROR] UnicodeDecodeError")
                    sjis += "|"
                i += 2
        return sjis
    return ""


def writeInt(f, num):
    f.write(struct.pack("<i", num))


def writeUInt(f, num):
    f.write(struct.pack("<I", num))


def writeShort(f, num):
    f.write(struct.pack("<h", num))


def writeUShort(f, num):
    f.write(struct.pack("<H", num))


def writeByte(f, num):
    f.write(struct.pack("B", num))


def writeString(f, str):
    f.write(str.encode("ascii"))


def writeZero(f, num):
    for i in range(num):
        writeByte(f, 0)


def writeShiftJIS(f, str, writelen=True):
    if str == "":
        if writelen:
            writeShort(f, 1)
        writeByte(f, 0)
        return 1
    str = str.replace("’", "'").replace("“", "\"").replace("”", "\"")
    i = 0
    strlen = 0
    if writelen:
        lenpos = f.tell()
        writeShort(f, strlen)
    if ord(str[0]) < 256:
        # ASCII string
        while i < len(str):
            if i < len(str) - 1 and str[i+1] == "<":
                str = str[:i+1] + " " + str[i+1:]
            if i < len(str) - 4 and str[i+1] == "U" and str[i+2] == "N" and str[i+3] == "K" and str[i+4] == "(":
                str = str[:i+1] + " " + str[i+1:]
            char = str[i]
            if char == "<":
                code = str[i+1] + str[i+2]
                f.write(bytes.fromhex(code))
                i += 4
                strlen += 1
            elif char == "U" and i < len(str) - 4 and str[i+1] == "N" and str[i+2] == "K" and str[i+3] == "(":
                code = str[i+4] + str[i+5]
                f.write(bytes.fromhex(code))
                code = str[i+6] + str[i+7]
                f.write(bytes.fromhex(code))
                i += 9
                strlen += 2
            else:
                if i+1 == len(str):
                    bigram = char + " "
                else:
                    bigram = char + str[i+1]
                i += 2
                if bigram not in table:
                    if warning:
                        try:
                            print(" [WARNING] Bigram not found:", bigram, "in string", str)
                        except UnicodeEncodeError:
                            print(" [WARNING] Bigram not found in string", str)
                    bigram = "  "
                f.write(bytes.fromhex(table[bigram]))
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
        writeZero(f, 1)
        pos = f.tell()
        f.seek(lenpos)
        writeShort(f, strlen + 1)
        f.seek(pos)
    return strlen + 1


def isStringPointer(f):
    readByte(f)
    b2 = readByte(f)
    b3 = readByte(f)
    b4 = readByte(f)
    # print("Signature: " + hex(b1) + " " + hex(b2) + " " + hex(b3) + " " + hex(b4))
    if (b2 == 0 or b2 == 0x28 or b2 == 0x2A) and b3 == 0 and b4 == 0x10:
        return True
    return False


def getSection(f, title):
    f.seek(0)
    ret = {}
    found = title == ""
    for line in f:
        line = line.strip("\r\n")
        if not found and line.startswith("!FILE:" + title):
            found = True
        elif found:
            if line.startswith("!FILE:"):
                break
            elif line.find("=") > 0:
                split = line.split("=", 1)
                split[1] = split[1].split("#")[0]
                ret[split[0]] = split[1]
    return ret


def checkShiftJIS(first, second):
    # Based on https://www.lemoda.net/c/detect-shift-jis/
    status = False
    if (first >= 0x81 and first <= 0x84) or (first >= 0x87 and first <= 0x9f):
        if second >= 0x40 and second <= 0xfc:
            status = True
    elif first >= 0xe0 and first <= 0xef:
        if second >= 0x40 and second <= 0xfc:
            status = True
    return status


def detectShiftJIS(f):
    ret = ""
    while True:
        b1 = readByte(f)
        if ret != "" and b1 == 0:
            return ret
        if ret != "" and b1 in bincodes:
            ret += "<" + toHex(b1) + ">"
            continue
        b2 = readByte(f)
        if checkShiftJIS(b1, b2):
            f.seek(-2, 1)
            try:
                ret += f.read(2).decode("cp932").replace("〜", "～")
            except UnicodeDecodeError:
                if ret.count("UNK(") >= 5:
                    return ""
                ret += "UNK(" + toHex(b1) + toHex(b2) + ")"
        elif len(ret) > 0 and ret.count("UNK(") < 5:
            ret += "UNK(" + toHex(b1) + toHex(b2) + ")"
        else:
            return ""


def getColorDistance(c1, c2):
    (r1, g1, b1, a1) = c1
    (r2, g2, b2, a2) = c2
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def getPaletteIndex(palette, color, fixtrasp=False):
    if color[3] == 0:
        return 0
    for i in range(0 if fixtrasp else 1, len(palette)):
        if palette[i][0] == color[0] and palette[i][1] == color[1] and palette[i][2] == color[2]:
            return i
    if palette[0][0] == color[0] and palette[0][1] == color[1] and palette[0][2] == color[2]:
        return 0
    if debug:
        print("  Color", color, "not found, finding closest color ...")
    mindist = 0xFFFFFFFF
    disti = 0
    for i in range(1, len(palette)):
        distance = getColorDistance(color, palette[i])
        if distance < mindist:
            mindist = distance
            disti = i
    if debug:
        print("  Closest color:", palette[disti])
    return disti


def findBestPalette(palettes, colors):
    if len(palettes) == 1:
        return 0
    mindist = 0xFFFFFFFF
    disti = 0
    for i in range(len(palettes)):
        distance = 0
        for color in colors:
            singledist = 0xFFFFFFFF
            for palcolor in palettes[i]:
                singledist = min(singledist, getColorDistance(color, palcolor))
            distance += singledist
        if distance < mindist:
            mindist = distance
            disti = i
            if mindist == 0:
                break
    return disti


def drawPalette(pixels, palette, width, ystart=0):
    for x in range(len(palette)):
        j = width + ((x % 8) * 5)
        i = ystart + ((x // 8) * 5)
        for j2 in range(5):
            for i2 in range(5):
                pixels[j + j2, i + i2] = palette[x]
    return pixels


def decompress(f, size):
    # Code based on https://wiibrew.org/wiki/LZ77
    header = readUInt(f)
    length = header >> 8
    type = (header >> 4) & 0xF
    if debug:
        print("  Header:", toHex(header), "length:", length, "type:", type)
    if type != 1:
        print("  [ERROR] Unknown compression type", type)
        return bytes()
    dout = bytearray()
    while len(dout) < length:
        flags = struct.unpack("<B", f.read(1))[0]
        for i in range(8):
            if flags & 0x80:
                info = struct.unpack(">H", f.read(2))[0]
                num = 3 + ((info >> 12) & 0xF)
                # disp = info & 0xFFF
                ptr = len(dout) - (info & 0xFFF) - 1
                for i in range(num):
                    dout.append(dout[ptr])
                    ptr += 1
                    if len(dout) >= length:
                        break
            else:
                dout += f.read(1)
            flags <<= 1
            if len(dout) >= length:
                break
    return bytes(dout)


def loadTable():
    if os.path.isfile("table.txt"):
        with open("table.txt", "r") as ft:
            for line in ft:
                table[line[:2]] = line[3:7]

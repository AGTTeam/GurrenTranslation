import math
import struct
import crcmod

debug = False
warning = True


# File reading
class Stream(object):
    def __init__(self, fpath, mode):
        self.f = fpath
        self.mode = mode

    def __enter__(self):
        self.f = open(self.f, self.mode)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.f.close()

    def tell(self):
        return self.f.tell()

    def seek(self, pos, whence=0):
        self.f.seek(pos, whence)

    def read(self, n=-1):
        return self.f.read(n)

    def write(self, data):
        self.f.write(data)

    def readInt(self):
        return struct.unpack("<i", self.read(4))[0]

    def readUInt(self):
        return struct.unpack("<I", self.read(4))[0]

    def readShort(self):
        return struct.unpack("<h", self.read(2))[0]

    def readUShort(self):
        return struct.unpack("<H", self.read(2))[0]

    def readByte(self):
        return struct.unpack("B", self.read(1))[0]

    def readString(self, length):
        str = ""
        for i in range(length):
            byte = self.readByte()
            # These control characters can be found in texture names, replace them with a space
            if byte == 0x82 or byte == 0x86:
                byte = 0x20
            if byte != 0:
                str += chr(byte)
        return str

    def readNullString(self):
        str = ""
        while True:
            byte = self.readByte()
            if byte == 0:
                break
            else:
                str += chr(byte)
        return str

    def writeInt(self, num):
        self.f.write(struct.pack("<i", num))

    def writeUInt(self, num):
        self.f.write(struct.pack("<I", num))

    def writeShort(self, num):
        self.f.write(struct.pack("<h", num))

    def writeUShort(self, num):
        self.f.write(struct.pack("<H", num))

    def writeByte(self, num):
        self.f.write(struct.pack("B", num))

    def writeString(self, str):
        self.f.write(str.encode("ascii"))

    def writeZero(self, num):
        for i in range(num):
            self.writeByte(0)


def decompress(f, size):
    # Code based on https://wiibrew.org/wiki/LZ77
    header = f.readUInt()
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


def patchBanner(f, title):
    for i in range(6):
        # Write new text
        f.seek(576 + 256 * i)
        for char in title:
            f.writeByte(ord(char))
            f.writeByte(0x00)
        # Compute CRC
        f.seek(32)
        crc = crcmod.predefined.mkCrcFun("modbus")(f.read(2080))
        f.seek(2)
        f.writeUShort(crc)


# Strings
def toHex(byte):
    hexstr = hex(byte)[2:].upper()
    if len(hexstr) == 1:
        return "0" + hexstr
    return hexstr


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


def getSection(f, title, comment="#"):
    ret = {}
    found = title == ""
    try:
        f.seek(0)
        for line in f:
            line = line.strip("\r\n")
            if not found and line.startswith("!FILE:" + title):
                found = True
            elif found:
                if title != "" and line.startswith("!FILE:"):
                    break
                elif line.find("=") > 0:
                    split = line.split("=", 1)
                    split[0] = split[0].replace(" ", "　")
                    split[1] = split[1].split(comment)[0]
                    if split[0] not in ret:
                        ret[split[0]] = []
                    ret[split[0]].append(split[1].replace("’", "'").replace("‘", "'").replace("…", "...").replace("—", "-").replace("～", "~").replace("	", " "))
    except UnicodeDecodeError:
        return ret
    return ret


# Generic texture
def readPalette(p):
    return (((p >> 0) & 0x1f) << 3, ((p >> 5) & 0x1f) << 3, ((p >> 10) & 0x1f) << 3, 0xff)


def getColorDistance(c1, c2):
    (r1, g1, b1, a1) = c1
    (r2, g2, b2, a2) = c2
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def sumColors(c1, c2, a=1, b=1, c=2):
    (r1, g1, b1, a1) = c1
    (r2, g2, b2, a2) = c2
    return ((r1 * a + r2 * b) // c, (g1 * a + g2 * b) // c, (b1 * a + b2 * b) // c, a1)


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

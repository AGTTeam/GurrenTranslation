import math
import os
import shutil
import struct
import subprocess
import crcmod

debug = False
warning = True


# File reading
class Stream(object):
    def __init__(self, fpath, mode, little=True):
        self.f = fpath
        self.mode = mode
        self.endian = "<" if little else ">"

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
        return struct.unpack(self.endian + "i", self.read(4))[0]

    def readUInt(self):
        return struct.unpack(self.endian + "I", self.read(4))[0]

    def readShort(self):
        return struct.unpack(self.endian + "h", self.read(2))[0]

    def readUShort(self):
        return struct.unpack(self.endian + "H", self.read(2))[0]

    def readByte(self):
        return struct.unpack("B", self.read(1))[0]

    def readSByte(self):
        return struct.unpack("b", self.read(1))[0]

    def readBytes(self, n):
        ret = ""
        for i in range(n):
            ret += toHex(self.readByte()) + " "
        return ret

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
        self.f.write(struct.pack(self.endian + "i", num))

    def writeUInt(self, num):
        self.f.write(struct.pack(self.endian + "I", num))

    def writeShort(self, num):
        self.f.write(struct.pack(self.endian + "h", num))

    def writeUShort(self, num):
        self.f.write(struct.pack(self.endian + "H", num))

    def writeByte(self, num):
        self.f.write(struct.pack("B", num))

    def writeSByte(self, num):
        self.f.write(struct.pack("b", num))

    def writeString(self, str):
        self.f.write(str.encode("ascii"))

    def writeZero(self, num):
        for i in range(num):
            self.writeByte(0)


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


def getHeaderID(file):
    with Stream(file, "rb") as f:
        f.seek(12)
        return f.readString(6)


# Strings
def toHex(byte):
    hexstr = hex(byte)[2:].upper()
    if len(hexstr) == 1:
        return "0" + hexstr
    return hexstr


def isAscii(s):
    for i in range(len(s)):
        if ord(s[i]) >= 128:
            return False
    return True


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
            line = line.rstrip("\r\n")
            if not found and line.startswith("!FILE:" + title):
                found = True
            elif found:
                if title != "" and line.startswith("!FILE:"):
                    break
                elif line.find("=") > 0:
                    split = line.split("=", 1)
                    split[1] = split[1].split(comment)[0]
                    if split[0] not in ret:
                        ret[split[0]] = []
                    ret[split[0]].append(split[1].replace("’", "'").replace("‘", "'").replace("…", "...").replace("—", "-").replace("～", "~").replace("	", " "))
    except UnicodeDecodeError:
        return ret
    return ret


# Folders
def makeFolder(folder, clear=True):
    if clear:
        clearFolder(folder)
    os.mkdir(folder)


def clearFolder(folder):
    if os.path.isdir(folder):
        shutil.rmtree(folder)


def copyFolder(f1, f2):
    clearFolder(f2)
    shutil.copytree(f1, f2)


def copyFile(f1, f2):
    if os.path.isfile(f2):
        os.remove(f2)
    shutil.copyfile(f1, f2)


def makeFolders(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass


def execute(cmd, show=True):
    subprocess.call(cmd, stdout=None if (show or debug) else subprocess.DEVNULL, stderr=subprocess.STDOUT)


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


# Compression
def decompress(f, size):
    header = f.readUInt()
    length = header >> 8
    type = 0x10 if ((header >> 4) & 0xF == 1) else 0x11
    if debug:
        print("  Header:", toHex(header), "length:", length, "type:", type)
    if type == 0x10:
        return bytes(decompressRawLZSS10(f.read(), length))
    elif type == 0x11:
        return bytes(decompressRawLZSS11(f.read(), length))


def decompressBinary(infile, outfile):
    filelen = os.path.getsize(infile)
    footer = bytes()
    if infile.endswith("arm9.bin"):
        filelen -= 0x0C
    with Stream(infile, "rb") as fin:
        # Read footer
        if infile.endswith("arm9.bin"):
            fin.seek(filelen)
            footer = fin.read(0x0C)
        # Read compression info
        fin.seek(filelen - 8)
        header = fin.read(8)
        enddelta, startdelta = struct.unpack("<LL", header)
        padding = enddelta >> 0x18
        enddelta &= 0xFFFFFF
        decsize = startdelta + enddelta
        headerlen = filelen - enddelta
        # Read compressed data and reverse it
        fin.seek(headerlen)
        data = bytearray()
        data.extend(fin.read(enddelta - padding))
        data.reverse()
        # Decompress and reverse again
        uncdata = decompressRawLZSS10(data, decsize, True)
        uncdata.reverse()
        # Write uncompressed bin with header
        with Stream(outfile, "wb") as f:
            fin.seek(0)
            f.write(fin.read(headerlen))
            f.write(uncdata)
    return headerlen, footer


# https://github.com/magical/nlzss/blob/master/lzss3.py
def bits(b):
    return ((b >> 7) & 1, (b >> 6) & 1, (b >> 5) & 1, (b >> 4) & 1, (b >> 3) & 1, (b >> 2) & 1, (b >> 1) & 1, (b) & 1)


def decompressRawLZSS10(indata, decompressed_size, binary=False):
    data = bytearray()
    it = iter(indata)
    disp_extra = 3 if binary else 1

    while len(data) < decompressed_size:
        b = next(it)
        flags = bits(b)
        for flag in flags:
            if flag == 0:
                data.append(next(it))
            elif flag == 1:
                sha = next(it)
                shb = next(it)
                sh = (sha << 8) | shb
                count = (sh >> 0xc) + 3
                disp = (sh & 0xfff) + disp_extra

                for _ in range(count):
                    data.append(data[-disp])
            else:
                raise ValueError(flag)

            if decompressed_size <= len(data):
                break

    if len(data) != decompressed_size:
        print("[ERROR] decompressed size does not match the expected size")

    return data


def decompressRawLZSS11(indata, decompressed_size):
    data = bytearray()
    it = iter(indata)

    while len(data) < decompressed_size:
        b = next(it)
        flags = bits(b)
        for flag in flags:
            if flag == 0:
                data.append(next(it))
            elif flag == 1:
                b = next(it)
                indicator = b >> 4

                if indicator == 0:
                    # 8 bit count, 12 bit disp
                    # indicator is 0, don't need to mask b
                    count = (b << 4)
                    b = next(it)
                    count += b >> 4
                    count += 0x11
                elif indicator == 1:
                    # 16 bit count, 12 bit disp
                    count = ((b & 0xf) << 12) + (next(it) << 4)
                    b = next(it)
                    count += b >> 4
                    count += 0x111
                else:
                    # indicator is count (4 bits), 12 bit disp
                    count = indicator
                    count += 1

                disp = ((b & 0xf) << 8) + next(it)
                disp += 1

                try:
                    for _ in range(count):
                        data.append(data[-disp])
                except IndexError:
                    raise Exception(count, disp, len(data), sum(1 for x in it))
            else:
                raise ValueError(flag)

            if decompressed_size <= len(data):
                break

    if len(data) != decompressed_size:
        print("[ERROR] decompressed size does not match the expected size")

    return data

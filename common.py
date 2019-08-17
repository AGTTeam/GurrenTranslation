import struct
import math

debug = False
warning = True
codes = [ 0x0A, 0x09, 0xA5, 0x20 ]

def toHex(byte):
    hexstr = hex(byte)[2:].upper()
    if len(hexstr) == 1:
        return "0" + hexstr
    return hexstr

def readInt(f):
    return struct.unpack("<i", f.read(4))[0]
def readShort(f):
    return struct.unpack("<h", f.read(2))[0]
def readByte(f):
    return struct.unpack("B", f.read(1))[0]
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
                sjis += f.read(2).decode("shift-jis").replace("〜", "～")
                i += 2
        return sjis
    return ""

def writeInt(f, num):
    f.write(struct.pack("<i", num))
def writeShort(f, num):
    f.write(struct.pack("<h", num))
def writeByte(f, num):
    f.write(struct.pack("B", num))
def writeString(f, str):
    f.write(str.encode("ascii"))
def writeZero(f, num):
    for i in range(num):
        writeByte(f, 0)
def writeShiftJIS(f, str, table):
    if str == "":
        writeShort(f, 1)
        writeByte(f, 0)
        return 1
    i = 0
    strlen = 0
    lenpos = f.tell()
    writeShort(f, strlen)
    if ord(str[0]) < 256:
        # ASCII string
        while i < len(str):
            if i < len(str) - 1 and (str[i+1] == "<"):
                str = str[:i+1] + " " + str[i+1:]
            char = str[i]
            if char == "<":
                code = str[i+1] + str[i+2]
                i += 4
                f.write(bytes.fromhex(code))
                strlen += 1
            else:
                if i+1 == len(str):
                    bigram = char + " "
                else:
                    bigram = char + str[i+1]
                bigram = bigram.replace("’", "'").replace("“", "\"").replace("”", "\"")
                i += 2
                if bigram not in table:
                    if warning:
                        print(" [WARNING] Bigram not found: " + bigram)
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
    writeZero(f, 1)
    pos = f.tell()
    f.seek(lenpos)
    writeShort(f, strlen + 1)
    f.seek(pos)
    return strlen + 1
def writePointer(f, pointer, pointerdiff):
    newpointer = pointer
    for k,v in pointerdiff.items():
        if k < pointer:
            newpointer += v
    if debug:
        print("  Shifted pointer " + str(pointer+16) + " to " + str(newpointer+16))
    writeInt(f, newpointer)

def isStringPointer(f):
    b1 = readByte(f)
    b2 = readByte(f)
    b3 = readByte(f)
    b4 = readByte(f)
    #print("Signature: " + hex(b1) + " " + hex(b2) + " " + hex(b3) + " " + hex(b4))
    if (b2 == 0 or b2 == 0x28 or b2 == 0x2A) and b3 == 0 and b4 == 0x10:
        return True
    return False
def getSection(f, title):
    f.seek(0)
    ret = {}
    found = False
    for line in f:
        if not found and line.startswith("!FILE:" + title):
            found = True
        elif found:
            if line.startswith("!FILE:"):
                break
            elif line.find("=") > 0:
                split = line[:-1].split("=", 1)
                split[1] = split[1].split("#")[0]
                ret[split[0]] = split[1]
    return ret

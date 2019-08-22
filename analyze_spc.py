import sys
import codecs
import common

infolder = "work_NFP/SPC.NFP/" if "-p" in sys.argv else "extract_NFP/SPC.NFP/"
outfile = "analyze_spc.txt"
functions = {}
common.loadTable()
inversetable = {}
for bigram, code in common.table.items():
    inversetable[code] = bigram


def writeLine(out, pos, byte, line):
    pos -= 16
    function = ""
    if pos in functions:
        function = functions[pos] + "  "
        del functions[pos]
    out.write(str(pos).zfill(5) + " 0x" + common.toHex(byte) + ": " + line + " " + function + "  \n")


def readBytes(f, n):
    ret = ""
    for i in range(n):
        ret += common.toHex(common.readByte(f)) + " "
    return ret


with codecs.open(outfile, "w", "utf-8") as out:
    out.write(sys.argv[1] + "  \n")
    with open(infolder + sys.argv[1], "rb") as f:
        f.seek(12)  # "SCRP" + filesize + "CODE"
        codesize = common.readInt(f)
        if codesize > 10:
            f.seek(16 + codesize + 8)
            while True:
                function = common.readNullString(f)
                if function == "":
                    break
                # Read the pointers until we find 0
                i = 0
                while True:
                    pointer = common.readUInt(f)
                    if pointer == 0:
                        break
                    else:
                        if pointer in functions:
                            functions[pointer] += "," + function + "#" + str(i)
                        else:
                            functions[pointer] = function + "#" + str(i)
                    i += 1
            f.seek(16 + 6)
            while f.tell() < 16 + codesize - 2:
                pos = f.tell()
                byte = common.readByte(f)
                if byte == 0x10:
                    line = readBytes(f, 2)
                    f.seek(-2, 1)
                    convert = ""
                    if "-p" in sys.argv:
                        sjislen = common.readUShort(f)
                        try:
                            i = 0
                            while i < sjislen - 1:
                                strbyte = common.readByte(f)
                                if strbyte in common.codes:
                                    convert += "<" + common.toHex(strbyte) + ">"
                                    i += 1
                                else:
                                    f.seek(-1, 1)
                                    char = common.toHex(common.readUShort(f))
                                    convert += inversetable[char[-2:] + char[:-2]]
                                    i += 2
                        except KeyError:
                            convert = ""
                    if convert != "":
                        line += "\"" + convert + "\" "
                    else:
                        f.seek(pos + 1)
                        sjis = common.readShiftJIS(f)
                        if sjis != "":
                            line += "\"" + sjis + "\" "
                        else:
                            f.seek(pos + 1)
                            asciilen = common.readUShort(f)
                            asciistr = f.read(asciilen - 1)
                            line += "\"" + asciistr.decode("ascii").replace("\r", "").replace("\n", "") + "\" "
                    line += readBytes(f, 9)
                    writeLine(out, pos, byte, line)
                elif byte == 0x15:
                    line = readBytes(f, 2)
                    f.seek(-1, 1)
                    bytelen = common.readByte(f)
                    for i in range(bytelen):
                        line += readBytes(f, 8)
                    writeLine(out, pos, byte, line)
                elif byte in common.spccodes:
                    writeLine(out, pos, byte, readBytes(f, common.spccodes[byte]))
                else:
                    writeLine(out, pos, byte, "Unknown!")
            for k, v in functions.items():
                out.write("Missing function pointer", k, ":", v, " \n")

import codecs
import game
from hacktools import common


def writeLine(out, pos, byte, line, functions):
    pos -= 16
    function = ""
    if pos in functions:
        function = functions[pos] + "  "
        del functions[pos]
    out.write(str(pos).zfill(5) + " 0x" + common.toHex(byte, True) + ": " + line + " " + function + "\n")


def run(filename, processed=False):
    infolder = "data/work_NFP/SPC.NFP/" if processed else "data/extract_NFP/SPC.NFP/"
    outfile = "data/analyze_spc.txt"
    tablefile = "data/table.txt"
    common.loadTable(tablefile)
    functions = {}
    inversetable = {}
    for bigram, code in common.table.items():
        inversetable[code] = bigram

    common.logMessage("Analyzing", filename, "...")
    with codecs.open(outfile, "w", "utf-8") as out:
        out.write(filename + "\n")
        with common.Stream(infolder + filename, "rb") as f:
            f.seek(12)  # "SCRP" + filesize + "CODE"
            codesize = f.readUInt()
            if codesize > 10:
                f.seek(16 + codesize + 8)
                while True:
                    function = f.readNullString()
                    if function == "":
                        break
                    # Read the pointers until we find 0
                    i = 0
                    while True:
                        pointer = f.readUInt()
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
                    byte = f.readByte()
                    if byte == 0x10:
                        line = f.readBytes(2)
                        f.seek(-2, 1)
                        convert = ""
                        if processed:
                            sjislen = f.readUShort()
                            try:
                                i = 0
                                while i < sjislen - 1:
                                    strbyte = f.readByte()
                                    if strbyte in game.codes:
                                        convert += "<" + common.toHex(strbyte, True) + ">"
                                        i += 1
                                    else:
                                        f.seek(-1, 1)
                                        char = common.toHex(f.readByte(), True) + common.toHex(f.readByte(), True)
                                        convert += inversetable[char]
                                        i += 2
                            except KeyError:
                                convert = ""
                        if convert != "":
                            line += "\"" + convert + "\" "
                        else:
                            f.seek(pos + 1)
                            sjis = game.readShiftJIS(f)
                            if sjis != "":
                                line += "\"" + sjis + "\" "
                            else:
                                f.seek(pos + 1)
                                asciilen = f.readUShort()
                                asciistr = f.read(asciilen - 1)
                                line += "\"" + asciistr.decode("ascii").replace("\r", "").replace("\n", "") + "\" "
                        line += f.readBytes(9)
                        writeLine(out, pos, byte, line, functions)
                    elif byte == 0x15:
                        line = f.readBytes(2)
                        f.seek(-1, 1)
                        bytelen = f.readByte()
                        for i in range(bytelen):
                            line += f.readBytes(8)
                        writeLine(out, pos, byte, line, functions)
                    elif byte in game.spccodes:
                        writeLine(out, pos, byte, f.readBytes(game.spccodes[byte]), functions)
                    else:
                        writeLine(out, pos, byte, "Unknown!", functions)
                for k, v in functions.items():
                    out.write("Missing function pointer " + str(k) + ": " + str(v) + "\n")
    common.logMessage("Done! Open", outfile)

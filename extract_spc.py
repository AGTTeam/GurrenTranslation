import os
import codecs
import common

infolder = "extract_NFP/SPC.NFP/"
outfile = "spc_input.txt"

with codecs.open(outfile, "w", "utf-8") as out:
    for file in os.listdir(infolder):
        if not file.endswith(".SPC"):
            continue
        print("Processing " + file + " ...")
        first = True
        foundstrings = []
        with open(infolder + file, "rb") as f:
            f.seek(12)  # "SCRP" + filesize + "CODE"
            codesize = common.readInt(f)
            if codesize > 10:
                f.seek(6, 1)
                while f.tell() < 16 + codesize - 2:
                    pos = f.tell()
                    byte = common.readByte(f)
                    if byte == 0x10:
                        try:
                            sjis = common.readShiftJIS(f)
                            if sjis != "" and sjis not in foundstrings:
                                if common.debug:
                                    print(" Found string at " + str(pos) + " with length " + str(len(sjis)))
                                if first:
                                    first = False
                                    out.write("!FILE:" + file + "\n")
                                foundstrings.append(sjis)
                                out.write(sjis + "=\n")
                            f.seek(9, 1)
                        except UnicodeDecodeError:
                            print(" [ERROR] Unicode")
                    elif byte == 0x15:
                        f.seek(1, 1)
                        bytelen = common.readByte(f)
                        f.seek(8 * bytelen, 1)
                    elif byte in common.spccodes:
                        f.seek(common.spccodes[byte], 1)
                    elif common.debug:
                        print(" Unknown byte " + common.toHex(byte) + " at " + str(pos))

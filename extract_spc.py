import codecs
import os
import common
import common_game as game

infolder = "data/extract_NFP/SPC.NFP/"
outfile = "data/spc_output.txt"

print("Extracting SPC ...")
with codecs.open(outfile, "w", "utf-8") as out:
    for file in os.listdir(infolder):
        if not file.endswith(".SPC"):
            continue
        print(" Processing", file, "...")
        first = True
        with common.Stream(infolder + file, "rb") as f:
            f.seek(12)  # "SCRP" + filesize + "CODE"
            codesize = f.readUInt()
            if codesize > 10:
                f.seek(6, 1)
                while f.tell() < 16 + codesize - 2:
                    pos = f.tell()
                    byte = f.readByte()
                    if byte == 0x10:
                        try:
                            sjis = game.readShiftJIS(f)
                            if sjis != "":
                                if common.debug:
                                    print("  Found string at", pos, "with length", len(sjis))
                                if first:
                                    first = False
                                    out.write("!FILE:" + file + "\n")
                                out.write(sjis + "=\n")
                            f.seek(9, 1)
                        except UnicodeDecodeError:
                            print("  [ERROR] UnicodeDecodeError")
                    elif byte == 0x15:
                        f.seek(1, 1)
                        bytelen = f.readByte()
                        f.seek(8 * bytelen, 1)
                    elif byte in game.spccodes:
                        f.seek(game.spccodes[byte], 1)
                    elif common.debug:
                        print("  Unknown byte", common.toHex(byte), "at", pos)

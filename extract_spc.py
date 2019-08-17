import os
import codecs
import common

infolder = "work_NFP/SPC.NFP/"
outfile = "spc_input.txt"

with codecs.open(outfile, "w", "utf-8") as out:
    for file in os.listdir(infolder):
        # Skip these 2 weird files
        if file == "NULL.SPC" or file == "SCRINI.SET":
            continue
        print("Processing " + file + " ...")
        first = True
        foundstrings = []
        with open(infolder + file, "rb") as f:
            f.seek(12) # "SCRP" + filesize + "CODE"
            codesize = common.readInt(f)
            while f.tell() < 16 + codesize - 4:
                pos = f.tell()
                # Try to read a pointer
                pointer = common.readInt(f)
                if pointer not in foundstrings and pointer > 0 and pointer < codesize:
                    # Found a pointer, check if it points to a string
                    f.seek(pointer + 16)
                    if common.isStringPointer(f):
                        # Found a string
                        foundstrings.append(pointer)
                        sjis = common.readShiftJIS(f)
                        if sjis != "":
                            if common.debug:
                                print(" Found string at " + str(pointer + 16) + " with length " + str(len(sjis)))
                            if first:
                                first = False
                                out.write("!FILE:" + filename + "\n")
                            out.write(sjis + "=\n")
                f.seek(pos + 1)

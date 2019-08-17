import os
import codecs
import common

infile = "extract/arm9.bin"
outfile = "bin_input.txt"

with codecs.open(outfile, "w", "utf-8") as out:
    insize = os.path.getsize(infile)
    with open(infile, "rb") as f:
        # Skip the beginning of the file to avoid false-positives
        f.seek(990000)
        foundstrings = []
        while f.tell() < insize - 16:
            pos = f.tell()
            check = common.detectShiftJIS(f)
            if check != "" and len(check) > 1:
                if check not in foundstrings:
                    if common.debug:
                        print("Found string at " + str(pos))
                    foundstrings.append(check)
                    out.write(check + "=\n")
                pos = f.tell() - 1
            f.seek(pos + 1)

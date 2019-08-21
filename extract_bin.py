import os
import codecs
import common

infile = "extract/arm9.bin"
outfile = "bin_input.txt"
limit = True

with codecs.open(outfile, "w", "utf-8") as out:
    insize = os.path.getsize(infile)
    with open(infile, "rb") as f:
        # Skip the beginning and end of the file to avoid false-positives
        f.seek(992000 if limit else 900000)
        foundstrings = []
        while f.tell() < 1180000:
            pos = f.tell()
            if not limit or pos < 1010000 or pos > 1107700:
                check = common.detectShiftJIS(f)
                if check != "":
                    if check not in foundstrings:
                        if common.debug:
                            print("Found string at " + str(pos))
                        foundstrings.append(check)
                        out.write(check + "=\n")
                    pos = f.tell() - 1
            f.seek(pos + 1)

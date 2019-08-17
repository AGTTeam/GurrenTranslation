import os
import codecs
import common

binin = "extract/arm9.bin"
binout = "repack/arm9.bin"
binfile = "bin_input.txt"

print("Repacking BIN ...")
common.loadTable()

section = {}
with codecs.open(binfile, "r", "utf-8") as bin:
    section = common.getSection(bin, "")

insize = os.path.getsize(binin)
with open(binin, "rb") as fi:
    with open(binout, "r+b") as fo:
        fi.seek(990000)
        while fi.tell() < insize - 16:
            pos = fi.tell()
            check = common.detectShiftJIS(fi)
            if check in section and section[check] != "":
                if common.debug:
                    print(" Replacing string at " + str(pos))
                fo.seek(pos)
                common.writeShiftJIS(fo, section[check], False)
                pos = fi.tell() - 1
                if fo.tell() > pos:
                    print(" [ERROR] String " + section[check] + " is too long.")
                else:
                    common.writeZero(fo, pos - fo.tell())
            fi.seek(pos + 1)

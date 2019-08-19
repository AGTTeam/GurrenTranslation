import os
import codecs
import common
import shutil

binin = "extract/arm9.bin"
binout = "repack/arm9.bin"
binfile = "bin_input.txt"

print("Repacking BIN ...")
common.loadTable()

section = {}
with codecs.open(binfile, "r", "utf-8") as bin:
    section = common.getSection(bin, "")

if os.path.isfile(binout):
    os.remove(binout)
shutil.copyfile(binin, binout)

insize = os.path.getsize(binin)
with open(binin, "rb") as fi:
    with open(binout, "r+b") as fo:
        # Skip the beginning and end of the file to avoid false-positives
        fi.seek(992000)
        while fi.tell() < 1180000:
            pos = fi.tell()
            if pos < 1010000 or pos > 1107700:
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

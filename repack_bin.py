import codecs
import os
import shutil
import common

binin = "extract/arm9.bin"
binout = "repack/arm9.bin"
binfile = "bin_input.txt"
if os.path.isfile(binout):
    os.remove(binout)
shutil.copyfile(binin, binout)

section = {}
with codecs.open(binfile, "r", "utf-8") as bin:
    section = common.getSection(bin, "")

print("Repacking BIN ...")
common.loadTable()
insize = os.path.getsize(binin)
with open(binin, "rb") as fi:
    with open(binout, "r+b") as fo:
        # Skip the beginning and end of the file to avoid false-positives
        fi.seek(992000)
        while fi.tell() < 1180000:
            pos = fi.tell()
            if pos < 1010000 or pos > 1107700:
                check = common.detectShiftJIS(fi)
                if check in section and section[check][0] != "":
                    if common.debug:
                        print(" Replacing string at", pos)
                    fo.seek(pos)
                    common.writeShiftJIS(fo, section[check][0], False)
                    pos = fi.tell() - 1
                    if fo.tell() > pos:
                        common.writeZero(fo, 1)
                        print(" [ERROR] String", section[check][0], "is too long.")
                    else:
                        common.writeZero(fo, pos - fo.tell())
            fi.seek(pos + 1)

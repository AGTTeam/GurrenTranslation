import codecs
import os
import struct
import common
import common_game as game

binin = "data/extract/arm9.bin"
binout = "data/repack/arm9.bin"
binfile = "data/bin_input.txt"
if not os.path.isfile(binfile):
    print("Input file", binfile, "not found.")
    quit()
common.copyFile(binin, binout)

freeranges = [(0xEA810, 0xEEC00)]
currentrange = 0
rangepos = 0

section = {}
with codecs.open(binfile, "r", "utf-8") as bin:
    section = common.getSection(bin, "")

print("Repacking BIN ...")
game.loadTable()
insize = os.path.getsize(binin)
rangepos = freeranges[currentrange][0]
with common.Stream(binin, "rb") as fi:
    allbin = fi.read()
    with common.Stream(binout, "r+b") as fo:
        # Skip the beginning and end of the file to avoid false-positives
        fi.seek(992000)
        while fi.tell() < 1180000:
            pos = fi.tell()
            if pos < 1010000 or pos > 1107700:
                check = game.detectShiftJIS(fi)
                if check in section and section[check][0] != "":
                    if common.debug:
                        print(" Replacing string at", pos)
                    fo.seek(pos)
                    endpos = fi.tell() - 1
                    newlen = game.writeShiftJIS(fo, section[check][0], False, endpos - pos)
                    if newlen < 0:
                        if rangepos >= freeranges[currentrange][1] and common.warning:
                            print("  [WARNING] No more room! Skipping ...")
                        else:
                            # Write the string in a new portion of the rom
                            if common.debug:
                                print("  No room for the string, redirecting to", rangepos)
                            fo.seek(rangepos)
                            game.writeShiftJIS(fo, section[check][0], False)
                            fo.writeZero(1)
                            newpointer = 0x02000000 + rangepos
                            rangepos = fo.tell()
                            # Search and replace the old pointer
                            pointer = 0x02000000 + pos
                            pointersearch = struct.pack("<I", pointer)
                            index = 0
                            while index < len(allbin):
                                index = allbin.find(pointersearch, index)
                                if index < 0:
                                    break
                                if common.debug:
                                    print("  Replaced pointer at", str(index))
                                fo.seek(index)
                                fo.writeUInt(newpointer)
                                index += 4
                            if rangepos >= freeranges[currentrange][1]:
                                if currentrange + 1 < len(freeranges):
                                    currentrange += 1
                                    rangepos = freeranges[currentrange][0]
                    else:
                        fo.writeZero(endpos - fo.tell())
            fi.seek(pos + 1)

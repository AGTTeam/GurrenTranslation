import shutil
import os
import codecs
import common

spcin = "extract_NFP/SPC.NFP/"
spcout = "work_NFP/SPC.NFP/"
if os.path.isdir(spcout):
    shutil.rmtree(spcout)
os.mkdir(spcout)
spcfile = "spc_input.txt"

print("Repacking SPC ...")
common.loadTable()

with codecs.open(spcfile, "r", "utf-8") as spc:
    for file in os.listdir(spcin):
        section = common.getSection(spc, file)
        # Skip Minigame files since they currently don't work
        if len(section) == 0 or file.startswith("MINI_"):
            shutil.copyfile(spcin + file, spcout + file)
        else:
            # Uncomment this line to enable the debug mode for only a specific file
            # common.debug = (file == "EV_004.SPC")
            if common.debug:
                print(" Repacking " + file + " ...")
            foundstrings = []
            pointerdiff = {}
            f = open(spcout + file, "wb")
            f.close()
            with open(spcout + file, "r+b") as f:
                with open(spcin + file, "rb") as fin:
                    common.writeString(f, "SCRP")
                    fin.seek(4)
                    common.writeInt(f, common.readInt(fin))
                    common.writeString(f, "CODE")
                    fin.seek(4, 1)
                    codesize = common.readInt(fin)
                    common.writeInt(f, codesize)
                    lastpos = fin.tell()
                    # Search for string pointers and shift them
                    while fin.tell() < 16 + codesize - 4:
                        pos = fin.tell()
                        pointer = common.readInt(fin)
                        if pointer not in foundstrings and pointer > 0 and pointer < codesize:
                            fin.seek(pointer + 16)
                            if common.isStringPointer(fin):
                                foundstrings.append(pointer)
                                oldlen = common.readShort(fin)
                                fin.seek(-2, 1)
                                sjis = common.readShiftJIS(fin)
                                # [TODO] A few files have unordered pointers
                                if lastpos >= pointer + 20:
                                    print("  [WARNING] Wrong order in file, skipping pointer")
                                else:
                                    # Copy the file up to here
                                    pos = fin.tell()
                                    fin.seek(lastpos)
                                    f.write(fin.read(pointer + 20 - lastpos))
                                    lastpos = pos + 7
                                    fixpointer = True
                                    if sjis != "":
                                        if common.debug:
                                            print("  Found SJIS string at pointer " + str(pointer+16))
                                        # Write the new string
                                        if sjis in section:
                                            newsjis = section[sjis]
                                            # If the string contains a |, try to turn the string into a 2-lines message
                                            if newsjis.find("|") > 0:
                                                newsjis = newsjis.replace("|", "<0A>")
                                                f.seek(-28, 1)
                                                common.writeByte(f, 2)
                                                f.seek(27, 1)
                                            newlen = common.writeShiftJIS(f, newsjis)
                                            lendiff = newlen - oldlen
                                            if lendiff != 0:
                                                if common.debug:
                                                    print("   Adding " + str(lendiff) + " at " + str(pointer - 4))
                                                pointerdiff[pointer + 4] = lendiff
                                        else:
                                            common.writeShiftJIS(f, sjis)
                                        common.writeByte(f, 0x22)
                                        common.writeByte(f, 0x00)
                                        if fixpointer:
                                            common.writePointer(f, pointer, pointerdiff)
                                        else:
                                            common.writeInt(f, pointer)
                                    else:
                                        if common.debug:
                                            print("  Found ASCII string at pointer " + str(pointer+16))
                                        # Copy the string up until the pointer
                                        asciilen = common.readShort(fin)
                                        common.writeShort(f, asciilen)
                                        asciistr = fin.read(asciilen)
                                        f.write(asciistr)
                                        common.writeByte(f, 0x22)
                                        common.writeByte(f, 0)
                                        common.writePointer(f, pointer, pointerdiff)
                        fin.seek(pos + 1)
                    # Copy the rest of the file
                    fin.seek(lastpos)
                    f.write(fin.read(codesize + 16 - lastpos))
                    endpos = f.tell()
                    # Search for code pointers
                    f.seek(16)
                    while f.tell() < endpos - 6:
                        pos = f.tell()
                        b1 = common.readByte(f)
                        b2 = common.readByte(f)
                        pointer = common.readInt(f)
                        if pointer > 0 and pointer < codesize:
                            found = False
                            if (b1 == 0x12 and b2 == 0x00) or (b1 == 0x00 and b2 == 0x11):  # or (b1 == 0x00 and b2 == 0x31):
                                fin.seek(pointer + 16)
                                b3 = common.readByte(fin)
                                b4 = common.readByte(fin)
                                if (b3 == 0x31 and b4 == 0x0F) or (b3 == 0x00 and b4 == 0x11):
                                    if common.debug:
                                        print("  Found code pointer " + str(pointer+16) + " at " + str(pos) + " with " + hex(b1) + ":" + hex(b2) + ":" + hex(b3) + ":" + hex(b4))
                                    found = True
                                elif common.debug:
                                    print("  Found possible code pointer " + str(pointer+16) + " at " + str(pos) + " with " + hex(b1) + ":" + hex(b2) + ":" + hex(b3) + ":" + hex(b4))
                            elif common.debug and (b1 != 0 or b2 != 0):
                                fin.seek(pointer + 16)
                                b3 = common.readByte(fin)
                                b4 = common.readByte(fin)
                                if b3 != 0 or b4 != 0:
                                    print("  Testing pointer " + str(pointer+16) + " at " + str(pos) + " with " + hex(b1) + ":" + hex(b2) + ":" + hex(b3) + ":" + hex(b4))
                            if found:
                                f.seek(pos + 2)
                                common.writePointer(f, pointer, pointerdiff)
                                pos += 6
                        f.seek(pos + 1)
                    # Write the code section size in the header
                    f.seek(12)
                    common.writeInt(f, endpos - 16)
                    f.seek(endpos)
                    # Function section
                    fin.seek(codesize + 16)
                    common.writeString(f, "FUNC")
                    fin.seek(4, 1)
                    funcsize = common.readInt(fin)
                    common.writeInt(f, funcsize)
                    # Copy the function section while shifting pointers
                    while True:
                        # Read the function name
                        function = ""
                        while True:
                            byte = common.readByte(fin)
                            if byte == 0:
                                break
                            else:
                                function += chr(byte)
                        if function == "":
                            break
                        common.writeString(f, function)
                        common.writeZero(f, 1)
                        if common.debug:
                            print("  Found function: " + function)
                        # Read the pointers until we find 0
                        while True:
                            pointer = common.readInt(fin)
                            if pointer == 0:
                                common.writeInt(f, 0)
                                break
                            else:
                                common.writePointer(f, pointer, pointerdiff)
                    common.writeZero(f, 1)
                    # Write the file size in the header
                    pos = f.tell()
                    f.seek(4)
                    common.writeInt(f, pos - 4)
                    f.seek(pos)
                    # Write TERM and pad with 0s
                    common.writeString(f, "TERM")
                    common.writeZero(f, 16 - (f.tell() % 16))

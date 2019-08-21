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


def writePointer(f, pointer, pointerdiff):
    newpointer = pointer
    for k, v in pointerdiff.items():
        if k < pointer:
            newpointer += v
    if common.debug and newpointer != pointer:
        print("   Shifted pointer " + str(pointer+16) + " to " + str(newpointer+16))
    common.writeInt(f, newpointer)


print("Repacking SPC ...")
common.loadTable()

with codecs.open(spcfile, "r", "utf-8") as spc:
    for file in os.listdir(spcin):
        section = common.getSection(spc, file)
        if len(section) == 0:
            shutil.copyfile(spcin + file, spcout + file)
            continue
        # Uncomment this line to enable the debug mode for only a specific file
        # common.debug = (file == "EV_004.SPC")
        # if common.debug:
        print(" Repacking " + file + " ...")
        codepointers = []
        pointerdiff = {}
        nextstr = ""
        f = open(spcout + file, "wb")
        f.close()
        with open(spcout + file, "r+b") as f:
            with open(spcin + file, "rb") as fin:
                # Write the header
                common.writeString(f, "SCRP")
                fin.seek(4)
                common.writeInt(f, common.readInt(fin))
                common.writeString(f, "CODE")
                fin.seek(4, 1)
                codesize = common.readInt(fin)
                common.writeInt(f, codesize)
                lastpos = fin.tell()
                f.write(fin.read(6))
                # Loop the file and shift pointers
                while fin.tell() < 16 + codesize - 2:
                    pos = fin.tell()
                    byte = common.readByte(fin)
                    common.writeByte(f, byte)
                    if byte == 0x10:
                        oldlen = common.readUShort(fin)
                        fin.seek(-2, 1)
                        strpos = fin.tell()
                        sjis = common.readShiftJIS(fin)
                        if (sjis != "" and sjis in section) or nextstr != "":
                            if common.debug:
                                print("  Found SJIS string at " + str(strpos + 16))
                            if nextstr == "":
                                if section[sjis] == "!":
                                    newsjis = ""
                                elif section[sjis] != "":
                                    newsjis = section[sjis]
                                else:
                                    newsjis = sjis
                            else:
                                newsjis = nextstr
                                nextstr = ""

                            # If the string contains a |, try to turn the string into a 2-lines message
                            if newsjis.find("|") > 0:
                                # First, search if we have an empty string after
                                savepos = fin.tell()
                                fin.seek(9, 1)
                                b1 = common.readByte(fin)
                                b2 = common.readByte(fin)
                                fin.seek(savepos)
                                if b1 == 0x10 and b2 == 0x01:
                                    splitstr = newsjis.split("|")
                                    newsjis = splitstr[0]
                                    nextstr = splitstr[1]
                                else:
                                    # Otherwise, change a byte to 2
                                    newsjis = newsjis.replace("|", "<0A>")
                                    f.seek(-28, 1)
                                    common.writeByte(f, 2)
                                    f.seek(27, 1)
                            newlen = common.writeShiftJIS(f, newsjis)
                            lendiff = newlen - oldlen
                            if lendiff != 0:
                                if common.debug:
                                    print("   Adding " + str(lendiff) + " at " + str(strpos))
                                pointerdiff[strpos - 16] = lendiff
                            fin.seek(1, 1)
                        else:
                            if common.debug:
                                print("  Found ASCII or unaltered string at " + str(strpos + 16))
                            fin.seek(strpos)
                            f.write(fin.read(oldlen + 2))
                        f.write(fin.read(2))
                        pointer = common.readUInt(fin)
                        writePointer(f, pointer, pointerdiff)
                    elif byte == 0x15:
                        f.write(fin.read(1))
                        bytelen = common.readByte(fin)
                        common.writeByte(f, bytelen)
                        for i in range(bytelen):
                            f.write(fin.read(4))
                            codepointers.append(f.tell())
                            f.write(fin.read(4))
                    elif byte in common.spccodes:
                        if byte == 0x11:
                            codepointers.append(f.tell())
                        elif byte == 0x12:
                            codepointers.append(f.tell() + 1)
                        f.write(fin.read(common.spccodes[byte]))
                    elif common.debug:
                        print(" Unknown byte " + common.toHex(byte) + " at " + str(pos))
                common.writeByte(f, 0x8F)
                common.writeByte(f, 0x00)
                common.writeByte(f, 0x00)
                endpos = f.tell()
                # Shift the other code pointers
                for codepointer in codepointers:
                    f.seek(codepointer)
                    pointer = common.readUInt(f)
                    f.seek(-4, 1)
                    writePointer(f, pointer, pointerdiff)
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
                    function = common.readNullString(fin)
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
                            writePointer(f, pointer, pointerdiff)
                common.writeZero(f, 1)
                # Write the file size in the header
                pos = f.tell()
                f.seek(4)
                common.writeInt(f, pos - 4)
                f.seek(pos)
                # Write TERM and pad with 0s
                common.writeString(f, "TERM")
                common.writeZero(f, 16 - (f.tell() % 16))

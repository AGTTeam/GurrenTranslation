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


def convertPointer(pointer, pointerdiff):
    newpointer = pointer
    for k, v in pointerdiff.items():
        if k < pointer:
            newpointer += v
    if common.debug and newpointer != pointer:
        print("   Shifted pointer", pointer + 16, "to", newpointer + 16)
    return newpointer


print("Repacking SPC ...")
common.loadTable()
with codecs.open(spcfile, "r", "utf-8") as spc:
    for file in os.listdir(spcin):
        section = common.getSection(spc, file)
        if len(section) == 0:
            shutil.copyfile(spcin + file, spcout + file)
            continue
        if common.debug:
            print(" Repacking", file, "...")
        codepointers = []
        pointerdiff = {}
        funcpointers = {"MswMess": [], "MswHit": []}
        nextstr = None
        addstr = ""
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
                        if (sjis != "" and sjis in section) or nextstr is not None:
                            if common.debug:
                                print("  Found SJIS string at", strpos + 16)
                            # Check if we have a nextstr to inject instead of using the section
                            if nextstr is None:
                                if section[sjis] == "!":
                                    newsjis = ""
                                elif section[sjis] != "":
                                    newsjis = section[sjis]
                                else:
                                    newsjis = sjis
                            else:
                                newsjis = nextstr
                                nextstr = None
                            # If the string starts with <<, pad it with spaces
                            if newsjis.startswith("<<"):
                                newsjis = newsjis[2:]
                                pad = " " * ((20 - len(newsjis)) // 2)
                                newsjis = pad + newsjis + pad
                            # If the string contains a >>, split it and save it for later
                            if newsjis.find(">>") > 0:
                                splitstr = newsjis.split(">>", 1)
                                newsjis = splitstr[0]
                                addstr = splitstr[1]
                            # Check if we have a string after
                            savepos = fin.tell()
                            fin.seek(9, 1)
                            b1 = common.readByte(fin)
                            b2 = common.readByte(fin)
                            fin.seek(savepos)
                            if b1 == 0x10 and b2 == 0x01:
                                nextstr = ""
                            # If the string contains a |, try to turn the string into a 2-lines message
                            if newsjis.find("|") > 0:
                                splitstr = newsjis.split("|", 1)
                                newsjis = splitstr[0]
                                nextstr = splitstr[1]
                                newsjis = newsjis.replace("|", "<0A>")
                                # Change the byte 0x1C bytes before the string to 2 if it's 1
                                f.seek(-28, 1)
                                checkbyte = common.readByte(f)
                                if checkbyte == 0x01:
                                    f.seek(-1, 1)
                                    common.writeByte(f, 2)
                                f.seek(27, 1)
                            # Write the SJIS string
                            newlen = common.writeShiftJIS(f, newsjis)
                            lendiff = newlen - oldlen
                            if lendiff != 0:
                                if common.debug:
                                    print("   Adding", lendiff, "at", strpos)
                                pointerdiff[strpos - 16] = lendiff
                            fin.seek(1, 1)
                        else:
                            if common.debug:
                                print("  Found ASCII or unaltered string at", strpos + 16)
                            fin.seek(strpos)
                            f.write(fin.read(oldlen + 2))
                        f.write(fin.read(2))
                        pointer = common.readUInt(fin)
                        common.writeUInt(f, convertPointer(pointer, pointerdiff))
                        # Check if we have an addstr
                        if addstr != "" and nextstr is None:
                            addstrsplit = addstr.split(">>")
                            for addstr in addstrsplit:
                                strsplit = addstr.split("|")
                                startpointer = f.tell()
                                startpointeri = fin.tell()
                                common.writeByte(f, 0x28)
                                common.writeByte(f, 0x00)
                                funcpointers["MswMess"].append(f.tell() - 16)
                                common.writeByte(f, 0x29)
                                common.writeUInt(f, 0x03)
                                common.writeByte(f, 0x80)
                                common.writeUInt(f, 0x00)
                                common.writeByte(f, 0x2A)
                                common.writeByte(f, 0x00)
                                common.writeByte(f, 0x31)
                                common.writeByte(f, 0x0F)
                                common.writeUInt(f, 0x0C)
                                common.writeByte(f, 0x29)
                                common.writeUInt(f, 0x00)
                                funcpointers["MswHit"].append(f.tell() - 16)
                                common.writeByte(f, 0x29)
                                common.writeUInt(f, 0x01)
                                common.writeByte(f, 0x80)
                                common.writeUInt(f, 0x00)
                                common.writeByte(f, 0x2A)
                                common.writeByte(f, 0x00)
                                common.writeByte(f, 0x31)
                                common.writeByte(f, 0x0F)
                                common.writeUInt(f, 0x04)
                                common.writeByte(f, 0x29)
                                common.writeUInt(f, 0x01)
                                common.writeByte(f, 0x10)
                                strpointer = f.tell()
                                common.writeShiftJIS(f, strsplit[0])
                                common.writeByte(f, 0x22)
                                common.writeByte(f, 0x00)
                                common.writeUInt(f, strpointer - 16 - 4)
                                common.writeByte(f, 0x28)
                                common.writeByte(f, 0x00)
                                common.writeByte(f, 0x10)
                                strpointer2 = f.tell()
                                common.writeShiftJIS(f, strsplit[1] if len(strsplit) == 2 else "")
                                common.writeByte(f, 0x22)
                                common.writeByte(f, 0x00)
                                common.writeUInt(f, strpointer2 - 16 - 4)
                                endpointer = f.tell()
                                if common.debug:
                                    print("   Adding new str", endpointer - startpointer, "at", startpointeri)
                                if startpointeri - 16 not in pointerdiff:
                                    pointerdiff[startpointeri - 16] = 0
                                pointerdiff[startpointeri - 16] += endpointer - startpointer
                            addstr = ""
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
                        print(" Unknown byte", common.toHex(byte), "at", pos)
                common.writeByte(f, 0x8F)
                common.writeByte(f, 0x00)
                common.writeByte(f, 0x00)
                endpos = f.tell()
                # Shift the other code pointers
                for codepointer in codepointers:
                    f.seek(codepointer)
                    pointer = common.readUInt(f)
                    f.seek(-4, 1)
                    common.writeUInt(f, convertPointer(pointer, pointerdiff))
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
                if common.debug:
                    print("  " + str(funcpointers))
                while True:
                    # Read the function name
                    function = common.readNullString(fin)
                    if function == "":
                        break
                    common.writeString(f, function)
                    common.writeZero(f, 1)
                    if common.debug:
                        print("  Found function:", function)
                    # Read the pointers until we find 0
                    while True:
                        pointer = common.readInt(fin)
                        if pointer == 0:
                            common.writeInt(f, 0)
                            break
                        else:
                            pointer = convertPointer(pointer, pointerdiff)
                            if function in funcpointers and len(funcpointers[function]) > 0:
                                for newpointer in funcpointers[function]:
                                    if common.debug:
                                        print("  ", function, "new:", newpointer, "poi:", pointer)
                                    if pointer > newpointer:
                                        common.writeUInt(f, newpointer)
                                        funcpointers[function].remove(newpointer)
                            common.writeUInt(f, pointer)
                common.writeZero(f, 1)
                # Write the file size in the header
                pos = f.tell()
                f.seek(4)
                common.writeInt(f, pos - 4)
                f.seek(pos)
                # Write TERM and pad with 0s
                common.writeString(f, "TERM")
                common.writeZero(f, 16 - (f.tell() % 16))

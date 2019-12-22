import codecs
import os
import game
from hacktools import common


def run():
    infolder = "data/extract_NFP/SPC.NFP/"
    outfolder = "data/work_NFP/SPC.NFP/"
    infile = "data/spc_input.txt"
    tablefile = "data/table.txt"
    chartot = transtot = 0

    if not os.path.isfile(infile):
        common.logError("Input file", infile, "not found.")
        return
    common.makeFolder(outfolder)

    common.logMessage("Repacking SPC from", infile, "...")
    common.loadTable(tablefile)
    with codecs.open(infile, "r", "utf-8") as spc:
        files = common.getFiles(infolder, [".SPC", ".SET"])
        for file in common.showProgress(files):
            section = common.getSection(spc, file, "#", game.fixchars)
            if len(section) == 0:
                common.copyFile(infolder + file, outfolder + file)
                continue
            chartot, transtot = common.getSectionPercentage(section, chartot, transtot)
            common.logDebug("Repacking", file, "...")
            codepointers = []
            pointerdiff = {}
            funcpointers = {"MswMess": [], "MswHit": []}
            nextstr = None
            addstr = ""
            last29 = []
            oldstrpos = 0
            f = open(outfolder + file, "wb")
            f.close()
            with common.Stream(outfolder + file, "r+b") as f:
                with common.Stream(infolder + file, "rb") as fin:
                    # Write the header
                    f.writeString("SCRP")
                    fin.seek(4)
                    f.writeUInt(fin.readUInt())
                    f.writeString("CODE")
                    fin.seek(4, 1)
                    codesize = fin.readUInt()
                    f.writeUInt(codesize)
                    f.write(fin.read(6))
                    # Loop the file and shift pointers
                    while fin.tell() < 16 + codesize - 2:
                        pos = fin.tell()
                        byte = fin.readByte()
                        f.writeByte(byte)
                        if byte == 0x10:
                            oldlen = fin.readUShort()
                            fin.seek(-2, 1)
                            strpos = fin.tell()
                            strposf = f.tell()
                            sjis = game.readShiftJIS(fin)
                            if (sjis != "" and sjis in section) or nextstr is not None:
                                common.logDebug("Found SJIS string at", strpos + 16)
                                # Check if we have a nextstr to inject instead of using the section
                                if nextstr is None:
                                    newsjis = section[sjis].pop(0)
                                    if len(section[sjis]) == 0:
                                        del section[sjis]
                                    if newsjis == "!":
                                        newsjis = ""
                                        # Center the line
                                        savestrpos = f.tell()
                                        f.seek(oldstrpos - 28)
                                        checkbyte = f.readByte()
                                        if checkbyte == 0x02:
                                            f.seek(-1, 1)
                                            f.writeByte(1)
                                        f.seek(savestrpos)
                                    elif newsjis == "":
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
                                b1 = fin.readByte()
                                b2 = fin.readByte()
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
                                    checkpos = 28
                                    if newsjis.startswith("FIX("):
                                        splitstr = newsjis.split(")", 1)
                                        newsjis = splitstr[1]
                                        checkpos = int(splitstr[0].replace("FIX(", ""))
                                    f.seek(-checkpos, 1)
                                    checkbyte = f.readByte()
                                    if checkbyte == 0x01:
                                        f.seek(-1, 1)
                                        f.writeByte(2)
                                    f.seek(checkpos - 1, 1)
                                # Write the SJIS string
                                newlen = game.writeShiftJIS(f, newsjis)
                                lendiff = newlen - oldlen
                                if lendiff != 0:
                                    common.logDebug("Adding", lendiff, "at", strpos)
                                    pointerdiff[strpos - 16] = lendiff
                                fin.seek(1, 1)
                            else:
                                common.logDebug("Found ASCII or unaltered string at", strpos + 16)
                                fixPos = pos - 16
                                # Patch RITT_02 to add Dayakka's missing text
                                if file == "RITT_02.SPC" and fixPos == 1775:
                                    fin.seek(strpos + oldlen + 2)
                                    f.writeUShort(0x09)
                                    f.writeString("APP_DAYA")
                                    f.writeByte(0x00)
                                    pointerdiff[strpos - 16] = 8
                                elif file == "RITT_02.SPC" and fixPos == 1810:
                                    fin.seek(strpos + oldlen + 2)
                                    f.writeUShort(0x09)
                                    f.writeString("DAYA_004")
                                    f.writeByte(0x00)
                                    pointerdiff[strpos - 16] = 8
                                elif file == "RITT_02.SPC" and fixPos == 1845:
                                    fin.seek(strpos + oldlen + 2)
                                    f.writeUShort(0x05)
                                    f.writeString("AWAY")
                                    f.writeByte(0x00)
                                    pointerdiff[strpos - 16] = 4
                                else:
                                    fin.seek(strpos)
                                    f.write(fin.read(oldlen + 2))
                            f.write(fin.read(2))
                            pointer = fin.readUInt()
                            f.writeUInt(common.shiftPointer(pointer, pointerdiff))
                            # Check if we have an addstr
                            if addstr != "" and nextstr is None:
                                addstrsplit = addstr.split(">>")
                                for addstr in addstrsplit:
                                    strsplit = addstr.split("|")
                                    startpointer = f.tell()
                                    startpointeri = fin.tell()
                                    f.writeByte(0x28)
                                    f.writeByte(0x00)
                                    funcpointers["MswMess"].append(f.tell() - 16)
                                    f.writeByte(0x29)
                                    f.writeUInt(0x03)
                                    f.writeByte(0x80)
                                    f.writeUInt(0x00)
                                    f.writeByte(0x2A)
                                    f.writeByte(0x00)
                                    f.writeByte(0x31)
                                    f.writeByte(0x0F)
                                    f.writeUInt(0x0C)
                                    f.writeByte(0x29)
                                    f.writeUInt(0x00)
                                    funcpointers["MswHit"].append(f.tell() - 16)
                                    f.writeByte(0x29)
                                    f.writeUInt(0x01)
                                    f.writeByte(0x80)
                                    f.writeUInt(0x00)
                                    f.writeByte(0x2A)
                                    f.writeByte(0x00)
                                    f.writeByte(0x31)
                                    f.writeByte(0x0F)
                                    f.writeUInt(0x04)
                                    f.writeByte(0x29)
                                    f.writeUInt(last29[len(last29) - 1])
                                    f.writeByte(0x10)
                                    strpointer = f.tell()
                                    game.writeShiftJIS(f, strsplit[0])
                                    f.writeByte(0x22)
                                    f.writeByte(0x00)
                                    f.writeUInt(strpointer - 16 - 4)
                                    f.writeByte(0x28)
                                    f.writeByte(0x00)
                                    f.writeByte(0x10)
                                    strpointer2 = f.tell()
                                    game.writeShiftJIS(f, strsplit[1] if len(strsplit) == 2 else "")
                                    f.writeByte(0x22)
                                    f.writeByte(0x00)
                                    f.writeUInt(strpointer2 - 16 - 4)
                                    endpointer = f.tell()
                                    common.logDebug("Adding new str", endpointer - startpointer, "at", startpointeri)
                                    if startpointeri - 16 not in pointerdiff:
                                        pointerdiff[startpointeri - 16] = 0
                                    pointerdiff[startpointeri - 16] += endpointer - startpointer
                                addstr = ""
                            oldstrpos = strposf
                        elif byte == 0x15:
                            f.write(fin.read(1))
                            bytelen = fin.readByte()
                            f.writeByte(bytelen)
                            for i in range(bytelen):
                                f.write(fin.read(4))
                                codepointers.append(f.tell())
                                f.write(fin.read(4))
                        elif byte in game.spccodes:
                            if byte == 0x11:
                                codepointers.append(f.tell())
                            elif byte == 0x12:
                                codepointers.append(f.tell() + 1)
                            elif byte == 0x29:
                                last29.append(fin.readUInt())
                                fin.seek(-4, 1)
                            # Patch SYS_046 and fix the disappearing cut-in sprites
                            fixPos = pos - 16
                            if file == "SYS_046.SPC" and byte == 0x29 and fixPos in [9660, 11356, 11915, 13108, 13646]:
                                f.writeUInt(0x0A)
                                fin.seek(4, 1)
                            else:
                                f.write(fin.read(game.spccodes[byte]))
                        common.logDebug("Unknown byte", common.toHex(byte), "at", pos)
                    f.writeByte(0x8F)
                    f.writeByte(0x00)
                    f.writeByte(0x00)
                    endpos = f.tell()
                    # Shift the other code pointers
                    for codepointer in codepointers:
                        f.seek(codepointer)
                        pointer = f.readUInt()
                        f.seek(-4, 1)
                        f.writeUInt(common.shiftPointer(pointer, pointerdiff))
                    # Write the code section size in the header
                    f.seek(12)
                    f.writeUInt(endpos - 16)
                    f.seek(endpos)
                    # Function section
                    fin.seek(codesize + 16)
                    f.writeString("FUNC")
                    fin.seek(4, 1)
                    funcsize = fin.readUInt()
                    f.writeUInt(funcsize)
                    # Copy the function section while shifting pointers
                    common.logDebug(str(funcpointers))
                    while True:
                        # Read the function name
                        function = fin.readNullString()
                        if function == "":
                            break
                        f.writeString(function)
                        f.writeZero(1)
                        common.logDebug("Found function:", function)
                        # Read the pointers until we find 0
                        while True:
                            pointer = fin.readUInt()
                            if pointer == 0:
                                f.writeUInt(0)
                                break
                            else:
                                pointer = common.shiftPointer(pointer, pointerdiff)
                                if function in funcpointers and len(funcpointers[function]) > 0:
                                    for newpointer in funcpointers[function]:
                                        common.logDebug(function, "new:", newpointer, "poi:", pointer)
                                        if pointer > newpointer:
                                            f.writeUInt(newpointer)
                                            funcpointers[function].remove(newpointer)
                                f.writeUInt(pointer)
                    f.writeZero(1)
                    # Write the file size in the header
                    pos = f.tell()
                    f.seek(4)
                    f.writeUInt(pos - 4)
                    f.seek(pos)
                    # Write TERM and pad with 0s
                    f.writeString("TERM")
                    f.writeZero(16 - (f.tell() % 16))
    common.logMessage("Done! Translation is at {0:.2f}%".format((100 * transtot) / chartot))

import codecs
import common
import os
import shutil
from PIL import Image

xmlfile = "fontdump.xml"
imgfile = "fontdump.png"
fontfile = "font.png"
outfile = "fontout.png"
infont = "extract_NFP/ETC.NFP/GL_12FNT.NFT"
tempfont = "GL_12FNT.NFTR"
outfont = "work_NFP/ETC.NFP/GL_12FNT.NFT"
binin = "bin_input.txt"
spcin = "spc_input.txt"
table = "table.txt"

# List of characters
upperchars = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
lowerchars = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
punctuation = [" ", "!", "?", "'", "\"", ",", ".", ":", ";", "(", ")", "-", "♪", "☆", "~", "%", "*", "&"]
customs = ["TEST"]
all = upperchars + lowerchars + numbers + punctuation

# X Position in the font.png file
positions = {}
for i in range(len(upperchars)):
    positions[upperchars[i]] = i * 12
    positions[lowerchars[i]] = (i * 12) + 6
for i in range(len(numbers)):
    positions[numbers[i]] = (len(upperchars) * 12) + (i * 6)
for i in range(len(punctuation)):
    positions[punctuation[i]] = (len(upperchars) * 12) + (len(numbers) * 6) + (i * 6)

# Fix the font size before dumping it
with open(infont, "rb") as font:
    with open(tempfont, "wb") as temp:
        font.seek(8)
        size = common.readUInt(font)
        font.seek(0)
        temp.write(font.read(size))
# Dump the font
os.system("NerdFontTerminatoR -e " + tempfont + " " + xmlfile + " " + imgfile)

# Generate the code range
coderanges = [(0x89, 0x9F), (0xE0, 0xEA)]
skipcodes = [0x7F]
charrange = (0x40, 0xFC)
codes = []
for coderange in coderanges:
    for i in range(coderange[0], coderange[1] + 1):
        first = charrange[0]
        if i == 0x88:
            first = 0x9F
        last = charrange[1]
        if i == 0xEA:
            last = 0xA4
        for j in range(first, last + 1):
            if j in skipcodes:
                continue
            hexcode = i * 0x100 + j
            if hexcode > 0x9872 and hexcode < 0x989F:
                continue
            codes.append(hexcode)

# Generate a basic bigrams list
items = ["  "]
for char1 in upperchars:
    for char2 in lowerchars:
        items.append(char1 + char2)
for char1 in upperchars:
    items.append(" " + char1)
    items.append(char1 + " ")
    for char2 in upperchars:
        if char1 + char2 not in items:
            items.append(char1 + char2)
for char1 in lowerchars:
    items.append(" " + char1)
    items.append(char1 + " ")
    for char2 in lowerchars:
        if char1 + char2 not in items:
            items.append(char1 + char2)
# And a complete one from all the bigrams
with codecs.open(spcin, "r", "utf-8") as spc:
    inputs = common.getSection(spc, "")
with codecs.open(binin, "r", "utf-8") as bin:
    inputs.update(common.getSection(bin, ""))
for k, input in inputs.items():
    str = "<0A>".join(input.replace("|", "<0A>").split(">>"))
    if str.startswith("<<"):
        str = str[2:]
    i = 0
    while i < len(str):
        if i < len(str) - 1 and str[i+1] == "<":
            str = str[:i+1] + " " + str[i+1:]
        elif i < len(str) - 4 and str[i+1:i+5] == "UNK(":
            str = str[:i+1] + " " + str[i+1:]
        char = str[i]
        if char == "<" and i < len(str) - 3 and str[i+3] == ">":
            i += 4
        elif char == "U" and i < len(str) - 4 and str[i+1:i+4] == "NK(":
            i += 9
        else:
            if i + 1 == len(str):
                bigram = char + " "
            else:
                bigram = char + str[i+1]
            i += 2
            if bigram not in items:
                if bigram[0] not in all or bigram[1] not in all:
                    print("Invalid bigram", bigram, "from phrase", str)
                else:
                    items.append(bigram)

# Open the images
img = Image.open(imgfile)
pixels = img.load()
font = Image.open(fontfile)
fontpixels = font.load()

# Generate the image and table
fontx = 106
fonty = 5644
x = len(codes) - 1
tablestr = ""
for item in reversed(items):
    for i2 in range(5):
        for j2 in range(11):
            pixels[fontx + i2, fonty + j2] = fontpixels[positions[item[0]] + i2, j2]
    for j2 in range(11):
        pixels[fontx + 5, fonty + j2] = fontpixels[positions[" "], j2]
    for i2 in range(5):
        for j2 in range(11):
            pixels[fontx + i2 + 6, fonty + j2] = fontpixels[positions[item[1]] + i2, j2]
    fontx -= 13
    if fontx < 0:
        fontx = 197
        fonty -= 13
    tablestr = (item + "=" + common.toHex(codes[x]) + "\n") + tablestr
    x -= 1
with codecs.open(table, "w", "utf-8") as f:
    f.write(tablestr)
img.save(outfile, "PNG")

# Generate the new font
os.system("NerdFontTerminatoR -i " + xmlfile + " " + outfile + " " + tempfont)
shutil.copyfile(tempfont, outfont)
# Clean up the temp files
os.remove(xmlfile)
os.remove(imgfile)
os.remove(outfile)
os.remove(tempfont)

print("All done!")

if x < len(items):
    print("Couldn't fit", len(items) - x, "bigrams")
else:
    print("Room for", x - len(items), "more bigrams")

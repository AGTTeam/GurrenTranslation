import shutil
import os
import common
from PIL import Image

dgin = "extract_NFP/NFP3D.NFP/"
dgwork = "work_3DG/"
dgout = "work_NFP/NFP3D.NFP/"
if os.path.isdir(dgout):
    shutil.rmtree(dgout)
os.mkdir(dgout)
dgfile = "3dg_data.txt"

print("Repacking 3DG ...")

with open(dgfile, "r") as dg:
    for file in os.listdir(dgin):
        section = common.getSection(dg, file)
        shutil.copyfile(dgin + file, dgout + file)
        if len(section) == 0:
            continue
        for k, v in section.items():
            pngname = file.replace(".3DG", "") + "_" + k + ".png"
            texdata = v.split(",")
            texformat = int(texdata[0])
            texwidth = int(texdata[1])
            texheight = int(texdata[2])
            texsize = int(texdata[3])
            texoffset = int(texdata[4])
            if texformat != 7:
                palname = texdata[5]
                palsize = int(texdata[6])
                paloffset = int(texdata[7])
            if os.path.isfile(dgwork + pngname):
                print(" Repacking " + pngname + " ...")
                img = Image.open(dgwork + pngname)
                img = img.convert("RGBA")
                pixels = img.load()
                with open(dgout + file, "r+b") as f:
                    # Read palette
                    if texformat != 7:
                        f.seek(paloffset)
                        paldata = []
                        for i in range(palsize // 2):
                            p = common.readShort(f)
                            paldata.append(common.readPalette(p))
                    # Write new texture data
                    f.seek(texoffset)
                    # A3I5 Translucent Texture (3bit Alpha, 5bit Color Index)
                    if texformat == 1:
                        print(" [ERROR] Texture format 1 not implemented")
                    # 4-color Palette
                    elif texformat == 2:
                        print(" [ERROR] Texture format 2 not implemented")
                    # 16-color Palette
                    elif texformat == 3:
                        for i in range(texheight):
                            for j in range(0, texwidth, 2):
                                index2 = common.getPaletteIndex(paldata, pixels[j, i])
                                index1 = common.getPaletteIndex(paldata, pixels[j + 1, i])
                                common.writeByte(f, ((index1) << 4) | index2)
                    # 256-color Palette
                    elif texformat == 4:
                        for i in range(texheight):
                            for j in range(texwidth):
                                index = common.getPaletteIndex(paldata, pixels[j, i])
                                common.writeByte(f, index)
                    # 4x4-Texel Compressed Texture
                    elif texformat == 5:
                        print(" [ERROR] Texture format 5 not implemented")
                    # A5I3 Translucent Texture (5bit Alpha, 3bit Color Index)
                    elif texformat == 6:
                        print(" [ERROR] Texture format 6 not implemented")
                    # Direct Color Texture
                    elif texformat == 7:
                        print(" [ERROR] Texture format 7 not implemented")

from hacktools import common

animfiles = {
    2: "data/extract_NFP/NFP2D.NFP/AV03_01.YCE",
    5: "data/extract_NFP/NFP2D.NFP/AV09_01.YCE",
    6: "data/extract_NFP/NFP2D.NFP/AV02_05.YCE",
    8: "data/extract_NFP/NFP2D.NFP/AV05_02.YCE"
}


def run(file, addframes):
    infile = "data/extract_NFP/NFP2D.NFP/" + file
    outfile = "data/work_YCE/" + file

    common.logMessage("Expanding", infile, "to", outfile, "...")
    with common.Stream(outfile, "wb") as f:
        with common.Stream(infile, "rb") as fin:
            # Copy header
            f.write(fin.read(28))
            # Image number
            num = fin.readUInt()
            fin.seek(num * 4, 1)
            f.writeUInt(num + addframes)
            # Make room for the positions
            offsetpos = f.tell()
            for i in range(num + addframes):
                f.writeUInt(0)
            # Copy the existing images
            for i in range(num):
                newpos = f.tell()
                f.seek(offsetpos + i * 4)
                f.writeUInt(newpos - 24)
                f.seek(newpos)
                size = fin.readUInt()
                fin.seek(-4, 1)
                data = fin.read(size)
                f.write(data)
            # Add the new frames
            for i in range(num, num + addframes):
                newpos = f.tell()
                f.seek(offsetpos + i * 4)
                f.writeUInt(newpos - 24)
                f.seek(newpos)
                f.write(data)
        # Read the animation frames from another file
        animoffset = f.tell()
        with common.Stream(animfiles[num + addframes], "rb") as fin:
            fin.seek(20)
            animoffset2 = fin.readUInt()
            fin.seek(animoffset2)
            animsize = fin.readUInt()
            fin.seek(-4, 1)
            f.write(fin.read(animsize))
        totsize = f.tell()
        # Pad with 0s
        f.writeZero(16 - (f.tell() % 16))
        # Write new sizes and offsets
        f.seek(8)
        f.writeUInt(totsize)
        f.seek(20)
        f.writeUInt(animoffset)
        f.writeUInt(animoffset - 32)
    common.logMessage("Done!")

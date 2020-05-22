from hacktools import common


def readSampledCurve(f, startoff, type, samplefunc, add=0):
    startframe = f.readUShort()
    other = f.readUShort()
    endframe = other & 0b111111111111
    width = (other >> 12) & 0b11
    lograte = (other >> 14) & 0b11
    numsamples = 31  # int((endframe - startframe) / math.pow(2, lograte))
    samplesoff = f.readUInt() + startoff
    common.logDebug("  sampled curve", type, "startframe", startframe, "endframe", endframe, "width", width, "lograte", lograte, "numsamples", numsamples, "samplesoff", common.toHex(samplesoff))
    savepos = f.tell()
    f.seek(samplesoff)
    for i in range(numsamples):
        samplefunc(f, width, add)
    f.seek(savepos)


def readFP(f):
    return f.readInt() / 0x1000


def writeFP(f, n):
    f.writeInt(int(n * 0x1000))


def readSampledTransCurve(f, width, add=0):
    sample = readFP(f)
    if add != 0:
        f.seek(-4, 1)
        writeFP(f, sample + add)
    common.logDebug("   sample", sample)


def readTransCurve(f, startoff, type, constant, add=0):
    if constant:
        const = readFP(f)
        if add != 0:
            f.seek(-4, 1)
            writeFP(f, const + add)
        common.logDebug("  constant curve", type, const)
    else:
        readSampledCurve(f, startoff, type, readSampledTransCurve, add)


def readSampledRotCurve(f, width, add=0):
    sample = f.readUShort()
    common.logDebug("   sample", sample)


def readRotCurve(f, startoff, type, constant):
    if constant:
        const = f.readUShort()
        unk = f.readUShort()
        common.logDebug("  constant curve", type, const, unk)
    else:
        readSampledCurve(f, startoff, type, readSampledRotCurve)


def readSampledScaleCurve(f, width, add=0):
    sample = readFP(f)
    unk = readFP(f)
    common.logDebug("   sample", sample, unk)


def readScaleCurve(f, startoff, type, constant):
    if constant:
        const = readFP(f)
        unk = readFP(f)
        common.logDebug("  constant curve", type, const, unk)
    else:
        readSampledCurve(f, startoff, type, readSampledScaleCurve)


# https://github.com/scurest/nsbmd_docs/blob/master/nsbmd_docs.txt#L584
def run():
    common.logMessage("Patching JNT files ...")
    infiles = [
        "data/work_NFP/NFP3D.NFP/RSLT_WN.3DG",
        "data/work_NFP/NFP3D.NFP/RSLT_DW.3DG",
        "data/work_NFP/NFP3D.NFP/RSLT_LS.3DG"
    ]
    xtweaks = [
        [0, 50, -50, 0],
        [0, 50, -50, 0],
        [0, 0, 50, -50, 0]
    ]

    for j in range(len(infiles)):
        infile = infiles[j]
        common.logDebug("Processing", infile)
        with common.Stream(infile, "r+b") as f:
            all = f.read()
            # Find JNT
            jnt = all.find(b'\x4a\x4e\x54\x30')
            f.seek(jnt + 4)
            size = f.readUInt()
            common.logDebug(common.toHex(f.tell()), "size", size)
            for i in range(6):
                common.logDebug(common.toHex(f.tell()), "unk", f.readUInt())
            common.logDebug(common.toHex(f.tell()), "name", f.readString(16))
            anim = f.tell()
            common.logDebug(common.toHex(f.tell()), "header", f.readString(4))
            framesnum = f.readUShort()
            common.logDebug(common.toHex(f.tell()), "framesnum", framesnum)
            tracksnum = f.readUShort()
            common.logDebug(common.toHex(f.tell()), "tracksnum", tracksnum)
            unk = f.readUInt()
            common.logDebug(common.toHex(f.tell()), "unk", unk)
            pivotoff = f.readUInt() + anim
            common.logDebug(common.toHex(f.tell()), "pivotoff", common.toHex(pivotoff))
            matrixoff = f.readUInt() + anim
            common.logDebug(common.toHex(f.tell()), "matrixoff", common.toHex(matrixoff))
            trackoff = []
            for i in range(tracksnum):
                trackoff.append(f.readUShort() + anim)
            for i in range(tracksnum):
                f.seek(trackoff[i])
                common.logDebug("track", i, common.toHex(f.tell()))
                flags = f.readUShort()
                common.logDebug(common.toHex(f.tell()), "flags", common.toHex(flags))
                f.seek(2, 1)
                no_channels = (flags & 0b1)
                common.logDebug(" no_channels", no_channels)
                no_trans = (flags >> 1) & 0b11
                trans_x_constant = (flags >> 3) & 0b1
                trans_y_constant = (flags >> 4) & 0b1
                trans_z_constant = (flags >> 5) & 0b1
                common.logDebug(" no_trans", no_trans, "trans_x_constant", trans_x_constant, "trans_y_constant", trans_y_constant, "trans_z_constant", trans_z_constant)
                no_rot = (flags >> 6) & 0b11
                rot_constant = (flags >> 8) & 0b1
                common.logDebug(" no_rot", no_rot, "rot_constant", rot_constant)
                no_scale = (flags >> 9) & 0b11
                scale_x_constant = (flags >> 11) & 0b1
                scale_y_constant = (flags >> 12) & 0b1
                scale_z_constant = (flags >> 13) & 0b1
                common.logDebug(" no_scale", no_scale, "scale_x_constant", scale_x_constant, "scale_y_constant", scale_y_constant, "scale_z_constant", scale_z_constant)
                if no_trans == 0:
                    readTransCurve(f, anim, "transx", trans_x_constant == 1, xtweaks[j][i])
                    readTransCurve(f, anim, "transy", trans_y_constant == 1)
                    readTransCurve(f, anim, "transz", trans_z_constant == 1)
                if no_rot == 0:
                    readRotCurve(f, anim, "rot", rot_constant == 1)
                if no_scale == 0:
                    readScaleCurve(f, anim, "scalex", scale_x_constant == 1)
                    readScaleCurve(f, anim, "scaley", scale_y_constant == 1)
                    readScaleCurve(f, anim, "scalez", scale_z_constant == 1)
    common.logMessage("Done!")

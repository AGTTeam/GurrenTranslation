import os
from hacktools import common, nitro


def run():
    infolder = "data/extract_NFP/NFP3D.NFP/"
    workfolder = "data/work_3DG/"
    outfolder = "data/work_NFP/NFP3D.NFP/"
    common.makeFolder(outfolder)

    common.logMessage("Repacking 3DG from", workfolder, "...")
    files = common.getFiles(infolder, ".3DG")
    for file in common.showProgress(files):
        common.logDebug("Processing", file, "...")
        common.copyFile(infolder + file, outfolder + file)
        nsbmd = nitro.readNSBMD(infolder + file)
        if nsbmd is not None and len(nsbmd.textures) > 0:
            for texi in range(len(nsbmd.textures)):
                pngname = file.replace(".3DG", "") + "_" + nsbmd.textures[texi].name + ".png"
                if os.path.isfile(workfolder + pngname):
                    common.logDebug(" Repacking", pngname, "...")
                    nitro.writeNSBMD(outfolder + file, nsbmd, texi, workfolder + pngname)
    common.logMessage("Done!")

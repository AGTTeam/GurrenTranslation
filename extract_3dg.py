import os
from hacktools import common, nitro


def run():
    infolder = "data/extract_NFP/NFP3D.NFP/"
    outfolder = "data/out_3DG/"
    common.makeFolder(outfolder)

    common.logMessage("Extracting 3DG to", outfolder, "...")
    files = common.getFiles(infolder, ".3DG")
    for file in common.showProgress(files):
        common.logDebug("Processing", file, "...")
        nsbmd = nitro.readNSBMD(infolder + file)
        if nsbmd is not None and len(nsbmd.textures) > 0:
            common.makeFolders(outfolder + os.path.dirname(file))
            for texi in range(len(nsbmd.textures)):
                nitro.drawNSBMD(outfolder + file.replace(".3DG", "") + "_" + nsbmd.textures[texi].name + ".png", nsbmd, texi)
    common.logMessage("Done! Extracted", len(files), "files")

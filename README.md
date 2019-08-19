# Prerequisites
Install Python 3.7 https://www.python.org/downloads/  
Run "pip install pillow"  
# Extraction
Copy the rom as "rom.nds" inside this folder  
Use dsbuff or similar to extract everything in a new "extract" folder. There should be a data directory inside that with the NFP files  
Run "python extract_nfp.py" to extract the NFP files in the "extract_NFP" and "work_NFP" folder  
Run "python extract_spc.py" to extract the SPC lines in the "spc_input.txt" file  
Run "python extract_bin.py" to extract the BIN lines in the "bin_input.txt" file  
Run "python extract_3dg.py" to extract the 3DG textures in the "work_3DG" folder  
Run "python extract_kpc.py" to extract the KPC textures in the "work_KPC" folder  
Run "python extract_yce.py" to extract the KPC textures in the "work_YCE" folder  
# Font Editing
The font should be replaced in work_NFP/ETC.NFP/GL_12FNT.NFT  
A "table.txt" file is needed with each line in the format of "Bigram=Code", for example "Aa=996B"  
# Text Editing
Edit the "spc_input.txt" and "bin_input.txt" files  
Control codes are written as &lt;XX&gt; and they should be kept. &lt;0A&gt; is a line break, the other are currently unknown  
The bin_input file contains more codes in the format of UNK(XXXX), these should always be kept  
A "|" can be used to make a single-line message become a two-lines message  
# Image Editing
Edit the images in the "work_3DG", "work_KPC" and "work_YCE" folders. The palette on the right should be followed but the repacker will try to approximate other colors to the nearest one  
If one or more images are deleted from the textures folder, the corresponding file will be just copied when repacking  
# Repacking
Run "python repack.py"  
Use dsbuff or similar to repack everything from the repack folder  
# SPC File Format (WIP)
4 Magic (SCRP)  
4 File size  
4 Magic (CODE)  
4 Code size  
6 0x00 0x04 0x00 0x00 0x00 0x00
[...code...]  
3 0x8F 0x00 0x00
4 Magic (FUNC), Optional  
4 Func size  
[...func...]  
4 Magic (TERM)  
# STOP_001.SPC Code
29 00 00 00 00 < If this is changed to 1, the place name is not hidden  
29 01 00 00 00 *PlaceNameVisible*  
80 00 00 00 00 2A 00 31 0F 04 00 00 00  
29 07 00 00 00  
29 21 00 00 00  
29 00 00 00 00  
29 03 00 00 00 *ChrSet1*  
80 00 00 00 00 2A 00 31 0F 0C 00 00 00  
29 01 00 00 00  
29 00 00 00 00  
10 08 00 "BU01_01" 00 22 00 45 00 00 00 28 00  
29 03 00 00 00 *FaceLoad*  
80 00 00 00 00 2A 00 31 0F 0C 00 00 00  
29 00 00 00 00  
29 01 00 00 00 *FaceSet*  
81 00 00 00 00 2A 00 31 0F 04 00 00 00  
29 00 00 00 00  
29 12 00 00 00  
29 0A 00 00 00  
29 00 00 00 00  
29 00 10 00 00  
29 01 00 00 00  
29 06 00 00 00 *A3dObjMove1*  
80 00 00 00 00 2A 00 31 0F 18 00 00 00  
10 09 00 "MSW_A001" 00 22 00 B1 00 00 00 28 00  
29 00 00 00 00  
29 02 00 00 00 *MSG_TRUE*  
81 00 00 00 00 2A 00 31 0F 08 00 00 00  
29 01 00 00 00  
10 1B 00 "………カミナに挨拶しなきゃ" 00 22 00 E1 00 00 00 28 00  
29 02 00 00 00 *MswMess*  
80 00 00 00 00 2A 00 31 0F 08 00 00 00  
29 00 00 00 00  
29 01 00 00 00 *MswHit*  
80 00 00 00 00 2A 00 31 0F 04 00 00 00  
29 00 00 00 00 *MSG_HIDE*  
81 00 00 00 00 2A 00  
29 00 00 00 00  
29 12 00 00 00  
29 0A 00 00 00  
29 00 00 00 00  
29 00 00 00 00  
29 01 00 00 00  
29 06 00 00 00 *A3dObjMove2*  
80 00 00 00 00 2A 00 31 0F 18 00 00 00  
29 00 00 00 00  
29 01 00 00 00 *FaceFree*  
80 00 00 00 00 2A 00 31 0F 04 00 00 00  
29 00 00 00 00 *PlaceNameRedraw*  
80 00 00 00 00 2A 00  
29 07 00 00 00  
29 21 00 00 00  
29 01 00 00 00  
29 03 00 00 00 *ChrSet2*  
80 00 00 00 00 2A 00 31 0F 0C 00 00 00  
# STOP_001.SPC Functions
PlaceNameVisible(0x2901@11)  
ChrSet(0x2903@44, 0x2903@417)  
FaceLoad(0x2903@91)  
A3dObjMove(0x2906@162,0x2906@349)  
MswMess(0x2902@266)  
MswHit(0x2901@289)  
FaceFree(0x2901@372)  
PlaceNameRedraw(0x2900@390)  
FaceSet(0x2901@114)  
MSG_TRUE(0x2902@205)  
MSG_HIDE(0x2900@307)  

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
# Text Editing
Edit the "spc_input.txt" and "bin_input.txt" files  
Control codes are written as &lt;XX&gt; and they should be kept. &lt;0A&gt; is a line break, the other are currently unknown  
The bin_input file contains more codes in the format of UNK(XXXX), these should always be kept  
A "|" can be used to make a single-line message become a two-lines message  
# Image Editing
Edit the images in the "work_3DG" folder. The palette on the right should be followed but the repacker will try to approximate other colors to the nearest one.  
If one or more images are deleted from the textures folder, the corresponding file will be just copied when repacking.  
# Repacking
Run "python repack.py"  
Use dsbuff or similar to repack everything from the repack folder  

# Prerequisites
Install Python 3.7 https://www.python.org/downloads/  
Run "pip install pillow"  
# Extraction
Copy "ndstool.exe" inside this folder  
Copy the rom as "rom.nds" inside this folder  
Run "extract_rom.py" to extract the ROM in the "extract" folder with ndstool  
Run "extract_nfp.py" to extract the NFP files in the "extract_NFP" and "work_NFP" folder  
Run "extract_spc.py" to extract the SPC lines in the "spc_input.txt" file  
Run "extract_bin.py" to extract the BIN lines in the "bin_input.txt" file  
Run "extract_3dg.py" to extract the 3DG textures in the "work_3DG" folder and a "3dg_data.txt" file used by the repacker  
Run "extract_yce.py" to extract the YCE images in the "work_YCE" folder and a "yce_data.txt" file used by the repacker  
Run "extract_kpc.py" to extract the KPC images in the "work_KPC" folder  
# Font Editing
The font should be replaced in work_NFP/ETC.NFP/GL_12FNT.NFT  
A "table.txt" file is needed with each line in the format of "Bigram=Code", for example "Aa=996B"  
# Text Editing
Edit the "spc_input.txt" and "bin_input.txt" files  
Control codes are written as &lt;XX&gt; and they should be kept. &lt;0A&gt; is a line break, the other are currently unknown  
The bin_input file contains more codes in the format of UNK(XXXX), these should always be kept  
A "|" can be used to make a single-line message become a two-lines message  
If the translated line starts with "<<", the line will be padded with spaces at the beginning and end up to 20 characters, for buttons with centered kanji  
Comments can be added at the end of the lines by using #  
# Image Editing
Edit the images in the "work_3DG", "work_KPC" and "work_YCE" folders. The palette on the right should be followed but the repacker will try to approximate other colors to the nearest one  
If one or more images are deleted from the image folders, the corresponding files will be just copied when repacking  
# Repacking
Run "repack.py" to generate "rom_patched.nds"  
If you only want to repack NFP and patch the rom, you can use "repack.py -nfp"  
You can also use the following parameters to only repack specific types: -spc, -bin, -3dg, -kpc, -yce  
For example "repack.py -spc -bin" will only repack SPC, BIN, NFP and patch the rom  
The "-deb" parameter is also available and when used it will send the player to the Debug Map when starting a new game  

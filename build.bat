pipenv run pyinstaller --clean --icon=icon.ico --add-binary "ndstool.exe;." --add-binary "armips.exe;." --add-binary "xdelta.exe;." --add-binary "NerdFontTerminatoR.exe;." --add-data "bin_patch.asm;." --distpath . -F --hidden-import="pkg_resources.py2_warn" tool.py
del tool.zip
7z a tool.zip tool.exe font.png fontconfig.txt

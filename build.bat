pyinstaller --clean --icon=icon.ico --add-binary "ndstool.exe;." --add-binary "xdelta.exe;." --add-binary "NerdFontTerminatoR.exe;." --distpath . -F --hidden-import="pkg_resources.py2_warn" tool.py
del tool.zip
7z a tool.zip tool.exe font.png fontconfig.txt

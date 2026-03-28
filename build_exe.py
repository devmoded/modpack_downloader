import subprocess
from pathlib import Path
# import sys

subprocess.run([
    'pyinstaller', '--noconfirm', '--onefile', '--windowed',
    '--name', 'modpack-downloader',
    '--paths', Path('src'),
    Path('src/modpack_downloader/main.py')
])

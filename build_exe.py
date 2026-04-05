import subprocess
from pathlib import Path
from sys import platform
from platformdirs import user_data_path

export_name = 'modpack-downloader'
if platform.startswith('linux'):
    export_name = 'modpack-downloader-linux'

print('Сборка исполняемого файла')
subprocess.run([
    'pyinstaller', '--noconfirm', '--onefile', '--windowed',
    '--name', export_name,
    '--paths', Path('src'),
    Path('src/modpack_downloader/main.py')
])
print('✅️ Сборка исполняемого файла завершена')

if platform.startswith('win'):
    iscc_path = user_data_path() / 'Programs' / 'Inno Setup 6' / 'ISCC.exe'
    if iscc_path.exists() and iscc_path.is_file():
        print('Сборка setup-файла через Inno Setup')
        compile_result = subprocess.run(
            [iscc_path, Path('setup.iss')],
            capture_output=True,
            text=True
        )
        print(compile_result.stdout)
        if compile_result.returncode != 0:
            print('❌️ Во время сборки setup-файла произошла ошибка')
            print(compile_result.stderr)
        else:
            print('✅️ Сборка setup-файла через Inno Setup завершена')

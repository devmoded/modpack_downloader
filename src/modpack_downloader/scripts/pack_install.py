# import json
import shutil

from pathlib import Path
# from string import Template

# from modpack_downloader.config import MODPACK_NAME

def install(modpack_content: Path):
    modpack_content.expanduser().resolve()
    if not modpack_content.exists():
        raise FileNotFoundError(f"{modpack_content} не существует!")
    modpack_info = modpack_content / 'modpack_info.json'
    # modpack_info_data = json.loads(modpack_info.read_text())

    # name = modpack_info_data['name']
    # version = modpack_info_data['version']
    # PACK_NAME = Template(MODPACK_NAME).substitute(name=name, version=version)

    modpack_root = modpack_content.parent
    main_content = modpack_content / 'main'
    # custom_content = modpack_content / 'custom'

    shutil.move(modpack_info, modpack_root / modpack_info.name)

    for m in main_content.iterdir():
        if m.name.startswith('mods') and (modpack_root / m.name).exists():
            shutil.rmtree(modpack_root / m.name)
            shutil.move(m, modpack_root / m.name)
        elif m.name.startswith('resourcepacks') and (modpack_root / m.name).exists():
            for item in m.iterdir():
                if modpack_root / m.name / item.name != m / item.name:
                    shutil.move(m / item.name, modpack_root / m.name/ item.name)
        else:
            shutil.move(m, modpack_root / m.name)
    shutil.rmtree(main_content)

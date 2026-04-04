import json
import yaml
import shutil
import requests

from pathlib import Path
from urllib.parse import urlparse, unquote

from modpack_downloader.core.api import API
from modpack_downloader.scripts.platforms_api import parse_modrinth

def install():
    modpack_content = API.get_modpack_content_path()
    modpack_info = modpack_content / 'modpack_info.json'

    modpack_root = modpack_content.parent
    shutil.move(modpack_info, modpack_root / modpack_info.name)

    instructions = _load_install_instructions()
    install_type = instructions.get('install_type')
    if install_type is None:
        raise RuntimeError('В \'instructions.yml\' не указано поле \'install_type\'')
    main_install = install_type.get('main')
    if main_install is None:
        raise RuntimeError('В \'instructions.yml\' не указано поле \'main\' в \'install_type\'')
    main_default = main_install.get('default')
    if main_default is None:
        raise RuntimeError('В \'instructions.yml\' не указано поле \'default\' в \'install_type/main\'')
    if main_default == 'force-copy':
        main_content = modpack_content / 'main'
        if not main_content.exists():
            raise FileNotFoundError(f"Каталог {main_content} не найден")

        for m in main_content.iterdir():
            if (modpack_root / m.name).exists():
                shutil.rmtree(modpack_root / m.name)
                shutil.move(m, modpack_root / m.name)
            else:
                shutil.move(m, modpack_root / m.name)
    main_mods = main_install.get('mods')
    if main_mods is not None:
        if main_mods == 'force-copy':
            _install_mods_via_copy(force=True)
        elif main_mods == 'from-list':
            _install_mods(force=False)
    main_resourcepacks = main_install.get('resourcepacks')
    if main_resourcepacks is not None:
        if main_resourcepacks == 'merge':
            _install_res_packs_via_merge()

    # shutil.rmtree(main_content)

def _load_install_instructions() -> dict:
    modpack_content = API.get_modpack_content_path()

    instructions_path = modpack_content / 'instructions.yml'
    return yaml.safe_load(instructions_path.read_text())

def _install_mods(force: bool = False):
    modpack_content = API.get_modpack_content_path()
    modpack_root = modpack_content.parent
    mods_path = modpack_root / 'mods'
    mods_path.mkdir(exist_ok=True, parents=True)

    mods_list = _load_mods_list()
    loader= mods_list.get('loader')
    mc_version = mods_list.get('mc_version')
    mods = mods_list.get('mods')

    if loader is None:
        raise RuntimeError('В \'mods_list.json\' не указано поле \'loader\'')
    if mc_version is None:
        raise RuntimeError('В \'mods_list.json\' не указано поле \'mc_version\'')
    if mods is None:
        raise RuntimeError('В \'mods_list.json\' не указано поле \'mods\'')

    for mod in mods:
        if isinstance(mod, dict) and isinstance(loader, str) and isinstance(mc_version, str):
            if mod['url'].startswith('https://modrinth.com'):
                API.set_status(('msg', f"Установка мода с Modrinth: {mod['name']}, {mod['version']}"))

                try:
                    download_url = parse_modrinth(loader, mc_version, mod['url'], mod['version'])
                except RuntimeError as e:
                    API.set_status(('err', f"Ошибка при установке мода с Modrinth: {mod['name']}: {e}"))
                else:
                    _download_file(download_url, mods_path, force)
            elif mod['url'].startswith('local:'):
                API.set_status(('msg', f"Копирование локального мода: {mod['name']}, {mod['version']}"))

                local_mod_path = modpack_content / mod['url'].replace('local:', '')
                mod_path = modpack_root / mods_path / local_mod_path.name
                if mod_path.exists() and not force:
                    API.set_status(('msg', f"Файл {mod_path} существует, пропускаю"))
                else:
                    shutil.move(local_mod_path, mod_path)

def _install_mods_via_copy(force: bool = False):
    modpack_content = API.get_modpack_content_path()

    modpack_root = modpack_content.parent
    main_content = modpack_content / 'main'
    if not main_content.exists():
        raise FileNotFoundError(f"Каталог {main_content} не найден")

    for m in main_content.iterdir():
        if m.name.startswith('mods'):
            if (modpack_root / m.name).exists() and force:
                shutil.rmtree(modpack_root / m.name)
                shutil.move(m, modpack_root / m.name)
            else:
                shutil.move(m, modpack_root / m.name)

def _install_res_packs_via_merge():
    modpack_content = API.get_modpack_content_path()

    modpack_root = modpack_content.parent
    main_content = modpack_content / 'main'
    if not main_content.exists():
        raise FileNotFoundError(f"Каталог {main_content} не найден")

    for m in main_content.iterdir():
        if m.name.startswith('resourcepacks'):
            if (modpack_root / m.name).exists():
                for item in m.iterdir():
                    if modpack_root / m.name / item.name != m / item.name:
                        shutil.move(m / item.name, modpack_root / m.name/ item.name)
            else:
                shutil.move(m, modpack_root / m.name)


def _load_mods_list() -> dict[str, str | list[dict[str, str]]]:
    modpack_content = API.get_modpack_content_path()
    mods_list_path = modpack_content / 'mods_list.json'
    if not mods_list_path.exists():
        raise FileNotFoundError(f"Список модов {mods_list_path} не существует")
    return json.loads(mods_list_path.read_text())


def _download_file(url: str, dst: Path, force: bool = False):
    filename = unquote(urlparse(url).path.split('/')[-1])
    file_path = dst / filename

    if file_path.exists() and not force:
        API.set_status(('msg', f"Файл {file_path} существует, пропускаю"))
    else:
        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(file_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        except requests.HTTPError as e:
            API.set_status(('err', f"Ошибка при скачивании файла {url}: {e}"))

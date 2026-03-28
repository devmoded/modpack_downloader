import requests
import zipfile
import json

# from datetime import datetime
from typing import Callable
from pathlib import Path
from string import Template

from modpack_downloader.config import MODPACK_NAME, INDEX_URL
from modpack_downloader.scripts.pack_install import install as post_download
# END_MESSAGE = 'Завершено'

class ModpackUtils:
    def __init__(
        self, modpack_info: dict[str, str],
        modpack_path: Path,
        status_callback: Callable,
        download_status_callback: Callable
    ):
        self.modpack_info = modpack_info
        self.name = modpack_info.get('name', '')
        self.version = modpack_info.get('version', '')
        self.source = modpack_info.get('source', '')
        self.status = status_callback
        self.dl_status = download_status_callback

        self.extract_path = modpack_path

    def _save_info_in_file(self):
        modpack_info = self.downloaded_pack / 'modpack_info.json'
        modpack_info_data = {'index_url': INDEX_URL, **self.modpack_info}
        modpack_info.write_text(json.dumps(modpack_info_data, indent=4))

    def _download_and_extract(self):
        """Скачивание сборки и её распаковка"""
        # load_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # pack_name = f"{self.name}-{self.version}-{load_time}"

        # Подстановка значений в имя файла сборки
        PACK_NAME = Template(MODPACK_NAME).substitute(name=self.name, version=self.version)

        tmp_path = self.extract_path / f"{PACK_NAME}-temp.zip"

        if not self.source:
            self.status(('msg', 'Поле \'source\' в информации о сборке не найдено'))
            return
        try:
            self.status(('msg', 'Скачивание сборки начато'))
            with requests.get(self.source, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('Content-Length', 0))
                downloaded = 0
                self.dl_status(('max', total_size))  # передаем максимум
                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            self.dl_status(('progress', downloaded))
        except requests.HTTPError as e:
            self.status(('msg', f"Ошибка при скачивании сборки: {e}"))
        else:
            self.dl_status(('done', ''))
            self.status(('msg', 'Скачивание сборки завершено'))
            self.downloaded_pack = self.extract_path / PACK_NAME

            try:
                with zipfile.ZipFile(tmp_path, "r") as zf:
                    zf.extractall(self.downloaded_pack)
            except zipfile.BadZipFile:
                self.status(('msg', "Ошибка: архив повреждён"))
            except OSError as e:
                self.status(('msg', f"Ошибка записи на диск: {e}"))
            else:
                tmp_path.unlink()
                self._save_info_in_file()
                self.status(('msg', f"Cборка '{self.name}' успешно скачана и распакована в {self.downloaded_pack}"))

    def _full_download(self):
        self._download_and_extract()

    def download_selected(self):
        self.status(('msg', 'Начато скачивание сборки'))
        self._full_download()
        # self._save_info_in_file() # TODO: решить, нужно ли сохранение информации о сборке
        try:
            self.status(('msg', f"Начало установки сборки '{self.name}'"))
            post_download(self.downloaded_pack)
        except FileNotFoundError as e:
            self.status(('msg', f"Ошибка установки сборки: {e}"))
        except Exception as e:
            self.status(('msg', f"Неизвестная ошибка во время установки: {e}"))
        else:
            self.status(('msg', f"Установка сборки '{self.name}' успешно завершена!"))
        self.status(('msg', f"Скачивание и установка сборки '{self.name}' завершена! Путь со сборкой: '{self.downloaded_pack}'"))
        self.status(('done', ''))

    # Для проверок функционала или дебага
    def print_selected(self):
        print(self.modpack_info)
        self.status(('done', ''))

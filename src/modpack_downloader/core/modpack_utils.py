import requests
import zipfile
import json

# from datetime import datetime
from typing import Callable
from pathlib import Path
from string import Template

from modpack_downloader.core.api import API
from modpack_downloader.core import index_utils
from modpack_downloader.config import MODPACK_NAME, INDEX_URL
from modpack_downloader.scripts.pack_install import install as post_download

class ModpackUtils:
    def __init__(
        self,
        modpack_path: Path,
        selected_modpack_name: str,
        download_status_callback: Callable
    ):
        self.modpack_info = index_utils.modpack_query(API.index_content, selected_modpack_name)
        self.name = self.modpack_info.get('name', '')
        self.version = self.modpack_info.get('version', '')
        self.source = self.modpack_info.get('source', '')
        self.dl_status = download_status_callback

        self.extract_path = modpack_path

    def _save_info_in_file(self):
        modpack_info = self.modpack_content / 'modpack_info.json'
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
            raise RuntimeError('Поле \'source\' в информации о сборке не найдено')
        try:
            API.set_status(('msg', 'Скачивание сборки начато'))
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
            raise RuntimeError(f"Ошибка при скачивании сборки: {e}")
        else:
            self.dl_status(('done', ''))
            API.set_status(('msg', 'Скачивание сборки завершено'))
            API.set_modpack_content_path(self.extract_path / PACK_NAME)

            self.modpack_content = API.get_modpack_content_path(for_unpack=True)

            try:
                with zipfile.ZipFile(tmp_path, "r") as zf:
                    zf.extractall(self.modpack_content)
            except zipfile.BadZipFile:
                raise RuntimeError("Ошибка: архив повреждён")
            except OSError as e:
                raise RuntimeError(f"Ошибка записи на диск: {e}")
            else:
                tmp_path.unlink()
                self._save_info_in_file()
                API.set_status(('msg', f"Cборка '{self.name}' успешно скачана и распакована в {self.modpack_content}"))

    def _full_download(self):
        self._download_and_extract()

    def download_selected(self):
        API.set_status(('msg', 'Начато скачивание сборки'))
        self._full_download()
        # self._save_info_in_file() # TODO: решить, нужно ли сохранение информации о сборке
        try:
            API.set_status(('msg', f"Начало установки сборки '{self.name}'"))
            post_download()
        except FileNotFoundError as e:
            API.set_status(('err', f"Ошибка установки сборки: {e}"))
        except RuntimeError as e:
            API.set_status(('err', f"Ошибка во время выполнения установки: {e}"))
        # except Exception as e:
        #     API.set_status(('err', f"Неизвестная ошибка во время установки: {e}"))
        else:
            API.set_status(('msg', f"Установка сборки '{self.name}' успешно завершена!"))
            API.set_status(('done', f"Скачивание и установка сборки '{self.name}' завершена! Путь со сборкой: '{self.modpack_content}'"))
        API.change_downloading_state(False)

    # Для проверок функционала или дебага
    def print_selected(self):
        print(self.modpack_info)
        API.set_status(('done', ''))

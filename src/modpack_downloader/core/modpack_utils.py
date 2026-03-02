import requests
import zipfile
import io
import json

from datetime import datetime
from typing import Callable
from platformdirs import user_downloads_path

END_MESSAGE = 'Завершено'

class ModpackUtils:
    def __init__(self, modpack_info: dict[str, str], status_callback: Callable):
        self.modpack_info = modpack_info
        self.name = modpack_info.get('name', '')
        self.version = modpack_info.get('version', '')
        self.source = modpack_info.get('source', '')
        self.status = status_callback

        self.downloads = user_downloads_path()

    def _save_info_in_file(self):
        modpack_info = self.downloaded_pack / 'modpack_info.json'
        modpack_info.write_text(json.dumps(self.modpack_info))

    def _download_and_extract(self):
        # Скачивание сборки и сохранение в оперативную память
        if not self.source:
            self.status('Поле \'source\' в информации о сборке не найдено')
            return
        try:
            self.status('Скачивание сборки начато')
            response = requests.get(self.source)
            response.raise_for_status()
        except requests.HTTPError as e:
            self.status(f"Ошибка при скачивании сборки: {e}")
        else:
            self.status('Скачивание сборки завершено')
            zip_bytes = io.BytesIO(response.content)

            load_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.downloaded_pack = self.downloads / f"{self.name}-{self.version}-{load_time}"

            try:
                with zipfile.ZipFile(zip_bytes) as zf:
                    zf.extractall(self.downloaded_pack)
            except zipfile.BadZipFile:
                self.status("Ошибка: архив повреждён")
            except OSError as e:
                self.status(f"Ошибка записи на диск: {e}")
            else:
                self.status(f"Cборка '{self.name}' успешно скачана и распакована в {self.downloaded_pack}")

    def _full_download(self):
        self._download_and_extract()

    def download_selected(self):
        self.status('Начато скачивание сборки')
        self._full_download()
        # self._save_info_in_file() # TODO: решить, нужно ли сохранение информации о сборке
        self.status(f"Скачивание сборки '{self.name}' завершено! Путь со сборкой: '{self.downloaded_pack}'")
        self.status(END_MESSAGE)

    # Для проверок функционала или дебага
    def print_selected(self):
        print(self.modpack_info)
        self.status(END_MESSAGE)

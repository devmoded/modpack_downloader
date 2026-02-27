import requests
import zipfile
import io
import shutil
import tempfile

from datetime import datetime
from typing import Callable
from pathlib import Path
from platformdirs import user_downloads_path

from modpack_loader.config import END_MESSAGE

class ModpackUtils:
    def __init__(self, modpack_info: dict[str, str], status_callback: Callable):
        self.modpack_info = modpack_info
        self.name = modpack_info.get('name', '')
        self.version = modpack_info.get('version', '')
        self.source = modpack_info.get('source', '')
        self.status = status_callback

        self.downloads = user_downloads_path()

        self.modpack_temp = None
        self.modpack_temp_path = None

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

            # Создание временного каталога
            self.modpack_temp = tempfile.TemporaryDirectory()
            self.modpack_temp_path = Path(self.modpack_temp.name)

            # Извлечение содержимого zip во временный каталог
            try:
                with zipfile.ZipFile(zip_bytes) as zf:
                    zf.extractall(self.modpack_temp_path)
            except zipfile.BadZipFile:
                self.status("Ошибка: архив повреждён")
            except OSError as e:
                self.status(f"Ошибка записи на диск: {e}")
            else:
                github_subdir = next(dir for dir in self.modpack_temp_path.iterdir() if dir.is_dir())
                for item in github_subdir.iterdir():
                    shutil.move(item, self.modpack_temp_path / item.name)

                github_subdir.rmdir()
                self.status(f"Cборка '{self.name}' успешно скачана и распакована в {self.modpack_temp_path}")

                shutil.move(self.modpack_temp_path, self.downloads)
                self.status(f"Cборка '{self.name}' перемещена из {self.modpack_temp_path} в {self.downloads}")

                load_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self.downloaded_pack = self.downloads / self.modpack_temp_path.name

                new_downloaded_pack_path = self.downloads / f"{self.name}-{self.version}-{load_time}"
                self.downloaded_pack.rename(new_downloaded_pack_path)
                self.downloaded_pack = new_downloaded_pack_path
                self.status(f"Cборка '{self.name}' переименована из {self.modpack_temp_path.name} в {self.downloaded_pack.name}")

    def _cleanup(self):
        # Очистка временного каталога
        if self.modpack_temp:
            self.status('Очистка начата')
            self.modpack_temp.cleanup()
            self.modpack_temp = None
            self.modpack_temp_path = None
            self.status('Временный каталог удалён')
            self.status('Очистка завершена')

    def _full_download(self):
        self._download_and_extract()
        self._cleanup()

    def download_selected(self):
        self.status('Начато скачивание сборки')
        self._full_download()
        self.status(f"Скачивание сборки '{self.name}' завершено! Путь со сборкой: '{self.downloaded_pack}'")
        self.status(END_MESSAGE)

    # Для проверок функционала или дебага
    def print_selected(self):
        print(self.modpack_info)
        self.status(END_MESSAGE)

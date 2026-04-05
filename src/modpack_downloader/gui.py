import tkinter as tk
import sys

from tkinter import ttk
from tkinter import filedialog
from threading import Thread
from queue import Queue, Empty
from pathlib import Path
from platformdirs import user_data_path

from modpack_downloader.core.api import API
from modpack_downloader.core import backend

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('Modpack Downloader')
        self.geometry('320x370')
        self.resizable(False, False)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.main_frame = MainFrame(self)
        self.main_frame.grid(row=0, column=0, sticky='nsew')

class MainFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=(45, 25))

        self.columnconfigure(0, weight=1)
        self.create_widgets()

        self.download_queue = Queue()

        API.init_in_gui(
            root_after=self.after,
            button_state_changer=self._change_downloading_state,
            status_print=self._set_status
        )
        API.start_status_checking()
        Thread(target=self._load_index, daemon=True).start()

    def _load_index(self):
        try:
            API.load_index()
            self.modpack_combo['values'] = API.modpacks_names
        except RuntimeError as e:
            API.set_status(('err', f"Не удалось загрузить индекс. Ошибка: {e}"))
        else:
            uri_data = backend.check_uri()
            if uri_data is not None:
                self.selected_modpack_name.set(uri_data['name'])
                self._start_download()

    def _set_status(self, status: str, fg: str = 'gray'):
        """Устанавливает текст статуса в надпись."""
        self.status_label.config(text=status, foreground=fg)

    def _change_downloading_state(self, is_downloading: bool):
        """Изменяет состояние кнопки загрузки в зависимости от состояния скачивания."""
        if is_downloading:
            self.download_button.config(state='disabled')
        else:
            self.download_button.config(state='normal')

    def _select_modpack_path(self):
        """Открывает диалог выбора папки с сборкой Minecraft и устанавливает выбранную папку в переменную."""
        versions_path = Path.home() # Значение по умолчанию
        if sys.platform.startswith('win'):
            versions_path = user_data_path(roaming=True) / '.minecraft' / 'versions'
        folder = filedialog.askdirectory(initialdir=versions_path, title='Выберите свою сборку')
        self.selected_modpack_path.set(folder)

    def _on_modpack_changed(self, *args):
        """Обновляет состояние кнопки загрузки в зависимости от выбранной сборки."""
        if self.selected_modpack_name.get():
            self.download_button.config(state='normal')
        else:
            self.download_button.config(state='disabled')

    def _start_download(self):
        # Выбор пути для загрузки и установки сборки
        self._select_modpack_path()
        if not self.selected_modpack_path.get():
            API.set_status(('msg', 'Отменено пользователем'))
            return

        API.change_downloading_state(True)

        backend.start_modpack_download(
            self.selected_modpack_name.get(), self.selected_modpack_path.get(),
            self.download_queue.put
        )
        self._update_download_progress_bar()

    # Подумать над вынесением в API
    def _update_download_progress_bar(self):
        try:
            while True:
                state, val = self.download_queue.get_nowait()
                if state == 'max':
                    self.progress_bar['maximum'] = val or 100
                elif state == 'progress':
                    self.progress_bar['value'] = val

                    # Сделать показ процентов загрузки получше чем этот кошмар
                    # progress = (val/self.progress_bar['maximum'])*100
                    # API.set_status(('msg', f"Загрузка: {round(progress, 2)}%"))
                elif state == 'done':
                    return
        except Empty:
            pass
        self.after(100, self._update_download_progress_bar)

    def create_widgets(self):
        # Поле с версией программы
        self.version_label = ttk.Label(
            self,
            text=f"Версия: {API.program_version}",
            font=('Segoe UI', 8)
        )
        self.version_label.grid(row=0, column=0, sticky='n', pady=(0, 5))

        self.title_label = ttk.Label(
            self,
            text='Выбор сборки',
            font=('Segoe UI', 14)
        )
        self.title_label.grid(row=1, column=0, sticky='n', pady=(0, 10))

        self.selected_modpack_path = tk.StringVar() # Путь до сборки
        self.selected_modpack_name = tk.StringVar() # Название выбранной сборки

        # При записи в `selected_modpack_name` вызываем `_on_modpack_changed`
        # Где проверяем не является ли `selected_modpack_name` пустым, и если
        # не является таковым, то делаем кнопку загрузки активной, иначе
        # блокируем её
        self.selected_modpack_name.trace_add('write', self._on_modpack_changed)

        # Выпадающий список доступных сборок
        self.modpack_combo = ttk.Combobox(
            self, textvariable=self.selected_modpack_name, state='readonly'
        )

        # - Список с доступными сборками
        self.modpack_combo.grid(row=2, column=0, sticky='ew')

        # Кнопка загрузки
        self.download_button = ttk.Button(
            self, text='Скачать', state='disabled',
            command=self._start_download
        )
        self.download_button.grid(row=3, column=0, pady=15)

        # Прогресс бар
        self.progress_bar = ttk.Progressbar(
            self, length=300, mode='determinate'
        )
        self.progress_bar.grid(row=4, column=0, pady=(0, 15))

        # Поле с состоянием работы программы
        self.status_label = ttk.Label(
            self, text='', foreground='gray', wraplength=210, justify='left'
        )
        self.status_label.grid(row=5, column=0, sticky='n')

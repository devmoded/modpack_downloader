import tkinter as tk
import threading
import sys

from tkinter import ttk
from tkinter import filedialog
from queue import Queue, Empty
from requests import HTTPError
from pathlib import Path
from platformdirs import user_data_path

from modpack_downloader.config import INDEX_URL
from modpack_downloader.core import index_utils
from modpack_downloader.core import link_parser
from modpack_downloader.core.modpack_utils import ModpackUtils

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
        super().__init__(parent, padding=45)

        self.columnconfigure(0, weight=1)
        self.create_widgets()

        self.status_queue = Queue()
        self._checking_queue = False

        self.download_queue = Queue()
        self._downloading = False
        self.index = None

        threading.Thread(target=self._load_index, daemon=True).start()

    def _check_uri(self):
        if len(sys.argv) > 1:
            uri = sys.argv[1]
            try:
                data = link_parser.parse_modpack_uri(uri)
            except RuntimeError as e:
                self._set_status(f"Ошибка: {e}")
            else:
                self.sel_modpack_name.set(data['name'])
                self._start_download()

    def _load_index(self):
        try:
            self.after(0, self._set_status, 'Загрузка индекса сборок')
            data = index_utils.get_index(INDEX_URL)
            self.after(0, self._on_index_loaded, data)
        except HTTPError as e:
            self.after(0, self._on_load_error, e)

    def _on_index_loaded(self, data):
        self.index = data
        modpacks_names = index_utils.get_modpacks_names(self.index, with_versions=True)
        if modpacks_names:
            self._set_status('Индекс успешно загружен. Выберите сборку')
            self.modpack_combo['values'] = modpacks_names
            self._check_uri()
        else:
            self._set_status('Ошибка: полученный список с именами сборок пуст')

    def _on_load_error(self, e):
        self._set_status(f"Ошибка при получении индекса сборок: {e}")

    def _set_status(self, status: str = ''):
        print(status)
        self.status_label.config(text=status)

    def _select_modpack_path(self):
        versions_path = Path.home()
        if sys.platform.startswith('win'):
            versions_path = user_data_path(roaming=True) / '.minecraft' / 'versions'
        folder = filedialog.askdirectory(initialdir=versions_path, title='Выберите свою сборку')
        self.modpack_path.set(folder)

    def _on_modpack_changed(self, *args):
        if self.sel_modpack_name.get():
            self.download_button.config(state='normal')
        else:
            self.download_button.config(state='disabled')

    def _downloader(self):
        self._set_status(f"Получение информации о сборке '{self.selected_modpack}'")
        modpack_info = index_utils.modpack_query(self.index, self.selected_modpack)

        if modpack_info:
            modpack_utils = ModpackUtils(
                modpack_info,
                modpack_path=Path(self.modpack_path.get()),
                status_callback=self.status_queue.put,
                download_status_callback=self.download_queue.put
            )
            self._update_download_progress()
            modpack_utils.download_selected()
            # modpack_utils.print_selected() # для проверок
        else:
            self._set_status(f"Информация о сборке '{self.selected_modpack}' пуста")

    def _start_download(self):
        if self._downloading:
            return

        self.selected_modpack = self.sel_modpack_name.get() # Получение названия выбранной сборки
        if not self.selected_modpack:
            self._set_status('Выберите сборку!')
            return
        self._select_modpack_path()
        if not self.modpack_path.get():
            self._set_status('Отменено пользователем')
            return

        self._downloading = True
        self.download_button.config(state='disabled')

        self._checking_queue = True
        threading.Thread(target=self._downloader, daemon=True).start()
        self._check_queue()

    def _update_download_progress(self):
        try:
            while True:
                kind, val = self.download_queue.get_nowait()
                if kind == 'max':
                    self.progress_bar['maximum'] = val or 100
                elif kind == 'progress':
                    self.progress_bar['value'] = val
                elif kind == 'done':
                    return
        except Empty:
            pass
        self.after(100, self._update_download_progress)

    def _check_queue(self):
        if not self._checking_queue:
            return
        try:
            while True:
                kind, msg = self.status_queue.get_nowait()

                if kind == 'msg':
                    self._set_status(msg)
                elif kind == 'done':
                    # Завершение загрузки (Выход из очереди)
                    self._checking_queue = False
                    self._downloading = False
                    self.download_button.config(state='normal')
                    return
        except Empty:
            pass
        self.after(100, self._check_queue)

    def create_widgets(self):
        # Поле с состоянием работы программы
        self.status_label = ttk.Label(
            self, text='', foreground='gray', wraplength=210, justify='left'
        )
        self.status_label.grid(row=4, column=0, sticky='n')

        self.title_label = ttk.Label(
            self,
            text='Выбор сборки',
            font=('Segoe UI', 14)
        )
        self.title_label.grid(row=0, column=0, sticky='n', pady=(0, 10))

        self.modpack_path = tk.StringVar() # Путь до сборки
        self.sel_modpack_name = tk.StringVar() # Название выбранной сборки
        self.sel_modpack_name.trace_add('write', self._on_modpack_changed)

        # Выпадающий список доступных сборок
        self.modpack_combo = ttk.Combobox(
            self, textvariable=self.sel_modpack_name, state='readonly'
        )

        # - Список с доступными сборками
        self.modpack_combo.grid(row=1, column=0, sticky='ew')

        self.progress_bar = ttk.Progressbar(
            self, length=300, mode='determinate'
        )
        self.progress_bar.grid(row=3, column=0, pady=(0, 15))

        # Кнопка установки
        self.download_button = ttk.Button(
            self, text='Скачать', state='disabled',
            command=self._start_download
        )
        self.download_button.grid(row=2, column=0, pady=15)

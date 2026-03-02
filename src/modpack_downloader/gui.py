import tkinter as tk
import threading

from tkinter import ttk
from queue import Queue
from requests import HTTPError

from modpack_downloader.config import INDEX_URL
from modpack_downloader.core import index_utils
from modpack_downloader.core.modpack_utils import ModpackUtils, END_MESSAGE

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
        self._downloading = False
        self.index = None

        threading.Thread(target=self._load_index, daemon=True).start()

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
        else:
            self._set_status('Ошибка: полученный список с именами сборок пуст')

    def _on_load_error(self, e):
        self._set_status(f"Ошибка при получении индекса сборок: {e}")

    def _set_status(self, status: str = ''):
        print(status)
        if status != END_MESSAGE:
            self.status_label.config(text=status)

    def _on_modpack_changed(self, *args):
        if self.sel_modpack_name.get():
            self.download_button.config(state='normal')
        else:
            self.download_button.config(state='disabled')

    def _start_download(self):
        if self._downloading:
            return

        self._downloading = True
        self.download_button.config(state='disabled')

        self._checking_queue = True
        threading.Thread(target=self._downloader, daemon=True).start()
        self._check_queue()

    def _downloader(self):
        selected = self.sel_modpack_name.get() # Получение названия выбранной сборки
        if not selected:
            self._set_status('Выберите сборку!')
            return

        self._set_status(f"Получение информации о сборке '{selected}'")
        modpack_info = index_utils.modpack_query(self.index, selected)

        if modpack_info:
            modpack_utils = ModpackUtils(
                modpack_info,
                status_callback=self.status_queue.put
            )
            modpack_utils.download_selected()
            # modpack_utils.print_selected() # для проверок
        else:
            self._set_status(f"Информация о сборке '{selected}' пуста")

    def _check_queue(self):
        if not self._checking_queue:
            return

        while not self.status_queue.empty():
            # Вывод текущего состояния
            message = self.status_queue.get()
            self._set_status(message)

            if message == END_MESSAGE:
                # Завершение загрузки (Выход из очереди)
                self._checking_queue = False
                self._downloading = False
                self.download_button.config(state='normal')
                # print('debug: Выход из очереди')

        self.after(100, self._check_queue)

    def create_widgets(self):
        # Поле с состоянием работы программы
        self.status_label = ttk.Label(
            self, text='', foreground='gray', wraplength=210, justify='left'
        )
        self.status_label.grid(row=3, column=0, sticky='n')

        self.title_label = ttk.Label(
            self,
            text='Выбор сборки',
            font=('Segoe UI', 14)
        )
        self.title_label.grid(row=0, column=0, sticky='n', pady=(0, 10))

        self.sel_modpack_name = tk.StringVar() # Название выбранной сборки
        self.sel_modpack_name.trace_add('write', self._on_modpack_changed)

        # Выпадающий список доступных сборок
        self.modpack_combo = ttk.Combobox(
            self, textvariable=self.sel_modpack_name, state='readonly'
        )

        # - Список с доступными сборками
        self.modpack_combo.grid(row=1, column=0, sticky='ew')

        # Кнопка установки
        self.download_button = ttk.Button(
            self, text='Скачать', state='disabled',
            command=self._start_download
        )
        self.download_button.grid(row=2, column=0, pady=15)

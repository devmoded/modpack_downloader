from typing import Callable
from queue import Queue, Empty
from requests import HTTPError

from modpack_downloader.config import INDEX_URL
from modpack_downloader.core import index_utils

class Api:
    def __init__(self):
        pass

    def init_in_gui(self, root_after: Callable,
        button_state_changer: Callable,
        status_print: Callable
    ):
        self.root_after = root_after
        self.change_downloading_state = button_state_changer
        self.status_print = status_print

    def _check_status(self):
        if self.status_queue is not None:
            try:
                while True:
                    state, msg = self.status_queue.get_nowait()

                    if state == 'msg':
                        print(f"INFO: {msg}")
                        self.status_print(msg)
                    elif state == 'done':
                        self.status_print(msg)
                        print(f"DONE: {msg}")
                        print('DEBUG: Выход из проверки статуса')
                        # Завершение загрузки (Выход из очереди)
                        # self._stop_status_checking()
            except Empty:
                pass
            self.root_after(100, self._check_status)

    def start_status_checking(self):
        self.status_queue = Queue()
        self.root_after(100, self._check_status)

    def _stop_status_checking(self):
        self.status_queue = None

    def set_status(self, status: tuple[str, str]):
        """
        Ожидает кортеж `status`состоящий из условных:
        - `state`: 'msg' или 'done'
        - `msg`: сообщение
        """
        if self.status_queue is not None:
            self.status_queue.put_nowait(status)
            # print(status)

    def load_index(self):
        self.set_status(('msg', 'Начало загрузки индекса'))
        try:
            self.index_content = index_utils.get_index(INDEX_URL)
        except HTTPError as e:
            raise RuntimeError(f"Ошибка при загрузке индекса: {e}")
        else:
            self.modpacks_names = index_utils.get_modpacks_names(self.index_content, with_versions=True)
            if self.modpacks_names:
                self.set_status(('msg', 'Индекс успешно загружен. Выберите сборку'))
            else:
                raise RuntimeError('Полученный список с именами сборок пуст')


API = Api()

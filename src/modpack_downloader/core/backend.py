from typing import Callable
from pathlib import Path
from threading import Thread
from sys import argv

from modpack_downloader.core.api import API
from modpack_downloader.core import link_parser
from modpack_downloader.core.modpack_utils import ModpackUtils

def check_uri() -> dict[str, str] | None:
    if len(argv) > 1:
        uri = argv[1]
        try:
            data = link_parser.parse_modpack_uri(uri)
        except RuntimeError as e:
            API.set_status(('msg', f"Ошибка: {e}"))
        else:
            return data

def start_modpack_download(
    selected_modpack_name: str, selected_modpack_path: str,
    download_callback: Callable
):
    API.set_status(('msg', f"Получение информации о сборке '{selected_modpack_name}'"))
    try:
        modpack_utils = ModpackUtils(
            modpack_path=Path(selected_modpack_path),
            selected_modpack_name=selected_modpack_name,
            download_status_callback=download_callback
        )
        Thread(
            target=modpack_utils.download_selected,
            daemon=True
        ).start()

    except RuntimeError as e:
        API.set_status(('done', f"Не удалось скачать сборку. Ошибка: {e}"))
        API.change_downloading_state(False)
    # modpack_utils.print_selected() # для проверок

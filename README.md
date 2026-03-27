Небольшой загрузчик для моих узкоспециализированных Minecraft сборок

Поддерживаемые сборки:
- [SPRRP](https://github.com/devmoded/SPRRP)

# Настройка
В `src/modpack_downloader/config.py` можно немного настроить программу:
- `INDEX_URL` - URL индекса со сборками. Описание индекса в 
[`docs/about_index.md`](https://github.com/devmoded/modpack_downloader/blob/main/docs/about_index.md)

# Минимальные требования:
- Python: [3.13](https://www.python.org/downloads/release/python-31312/)
  - `platformdirs`: 4.6.0
  - `requests`: 2.32.5
  - `tomli`: 2.4.0

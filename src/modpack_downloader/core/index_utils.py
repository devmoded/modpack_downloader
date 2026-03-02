import requests
import tomli

NAME_SEPARATOR = ' - '

def get_index(url: str) -> dict[str, list[dict[str, str]]]:
    response = requests.get(url)
    response.raise_for_status()
    data: dict[str, list[dict[str, str]]] = tomli.loads(response.text)
    return data

def get_modpacks_names(
    index: dict[str, list[dict[str, str]]] | None,
    with_versions: bool = False
) -> list[str]:

    names: list[str] = []
    if index:
        modpacks: list[dict[str, str]] = index.get('modpacks', [])
        if modpacks:
            for modpack in modpacks:
                name = modpack.get('name', '')
                version = modpack.get('version', '')

                if name:
                    if with_versions and version:
                        names.append(f"{name}{NAME_SEPARATOR}{version}")
                    else:
                        names.append(name)
    return names

def modpack_query(
    index: dict[str, list[dict[str, str]]] | None,
    query: str
) -> dict[str, str]:
    # TODO: может можно сделать как-либо лучше
    if NAME_SEPARATOR in query:
        name = query.split(NAME_SEPARATOR)[0]
    else:
        name = query

    if index:
        modpacks: list[dict[str, str]] = index.get('modpacks', [])
        if modpacks:
            for modpack in modpacks:
                if modpack.get('name') == name:
                    return modpack
    return {}

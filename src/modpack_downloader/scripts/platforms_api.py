import requests

def parse_modrinth_api(loader: str, mc_version: str, url: str, version: str) -> str:
    project_id = url.replace('https://modrinth.com/mod/', '')

    url = f"https://api.modrinth.com/v2/project/{project_id}/version"

    params = {
        'loaders': [loader],
        'game_versions': [mc_version],
        'include_changelog': 'false',
    }

    versions = requests.get(url, params=params, timeout=20).json()

    available_version = next(
        (
            v for v in versions
            # if v['version_number'].startswith(version)
            # TODO: Попытаться хоть как-то сделать сравнение версий
            if version.split('+')[0] in v['version_number']
            if loader in v['loaders']
            if mc_version in v['game_versions']
        ),
        None
    )

    if available_version is None:
        raise RuntimeError(f"Нет совпадений по версии для {url}")

    print('DEBUG: (сравнение версии)', available_version['version_number'], version in available_version['version_number'] )
    download_url = next(
        (f['url'] for f in available_version['files'] if f.get('primary')),
        available_version['files'][0]['url'],
    )

    return download_url

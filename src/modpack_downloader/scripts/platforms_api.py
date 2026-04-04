import requests

def parse_modrinth(loader: str, mc_version: str, url: str, version: str) -> str:
    project_id = url.replace('https://modrinth.com/mod/', '')

    url = f"https://api.modrinth.com/v2/project/{project_id}/version"

    params = {
        'loaders': loader,
        'game_versions': mc_version,
        'include_changelog': 'false',
    }

    # params = {
    #     'loaders': 'fabric',
    #     'game_versions': '1.21.1',
    #     'include_changelog': 'false',
    # }

    versions = requests.get(url, params=params, timeout=20).json()

    available_version = next(v for v in versions if v['version_number'] == version)

    download_url = next(
        (f['url'] for f in available_version['files'] if f.get('primary')),
        available_version['files'][0]['url'],
    )

    return download_url

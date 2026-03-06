from urllib.parse import urlparse

def parse_modpack_uri(uri: str) -> dict[str, str]:
    parsed = urlparse(uri)

    if parsed.scheme != 'modpack-dl':
        raise RuntimeError(f"Указана неизвестная схема URI: {parsed.scheme}")

    action = parsed.netloc
    parts = parsed.path.strip("/").split("/")

    if action == 'download':
        modpack_name = parts[0]
        # Поддержка загруки разных версий одной сборки пока отсутствует
        # modpack_version = parts[1] if len(parts) > 1 else 'latest'

        return {
            'action': action,
            'name': modpack_name,
            # 'version': modpack_version
        }

    raise RuntimeError(f"Указано неизвестное действие: {action}")

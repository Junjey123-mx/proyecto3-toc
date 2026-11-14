"""Lectura segura de archivos YAML con ``yaml.safe_load`` (PyYAML)."""

from pathlib import Path
from typing import Any

import yaml

from src.input.errors import YamlLoadError


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Lee ``path`` como un único documento YAML cuya raíz es un mapeo.

    ``safe_load`` solo construye tipos básicos (mapeos, listas, cadenas,
    números, booleanos y ``None``); las etiquetas que crearían objetos de Python
    se rechazan. La función no interpreta la máquina: eso es ``parse_machine``.
    """
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise YamlLoadError(f"{source}: no se puede leer el archivo ({error.strerror or error})") from error
    except UnicodeDecodeError as error:
        raise YamlLoadError(f"{source}: el archivo no está codificado en UTF-8 ({error.reason})") from error

    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise YamlLoadError(f"{source}: YAML inválido\n{error}") from error

    if document is None:
        raise YamlLoadError(f"{source}: el archivo no contiene un documento YAML")
    if not isinstance(document, dict):
        raise YamlLoadError(
            f"{source}: la raíz del documento debe ser un mapeo (q_states, alphabet, ...), "
            f"no {type(document).__name__}"
        )
    return document

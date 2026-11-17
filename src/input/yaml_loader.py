"""Lectura segura de archivos YAML con el ``SafeLoader`` de PyYAML."""

from collections.abc import Hashable
from pathlib import Path
from typing import Any

import yaml

from src.input.errors import YamlLoadError

_MERGE_TAG = "tag:yaml.org,2002:merge"


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """``SafeLoader`` que además rechaza claves repetidas dentro de un mismo mapeo.

    PyYAML conserva en silencio el último valor de una clave repetida, aunque
    YAML exige claves únicas. Hereda los constructores seguros sin cambios, así
    que, igual que ``yaml.safe_load``, nunca crea objetos de Python.
    """

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        """Construye el mapeo como ``SafeLoader``, pero antes rechaza las claves repetidas."""
        seen: set[Hashable] = set()
        for key_node, _ in node.value:
            # La clave de fusión ``<<`` no es un dato: SafeLoader la resuelve al combinar los mapeos.
            if key_node.tag == _MERGE_TAG:
                continue
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, Hashable):
                continue  # SafeLoader reporta las claves no hashables
            if key in seen:
                raise yaml.constructor.ConstructorError(
                    "al construir un mapeo", node.start_mark, f"clave repetida {key!r}", key_node.start_mark
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Lee ``path`` como un único documento YAML cuya raíz es un mapeo.

    ``yaml.safe_load(s)`` equivale a ``yaml.load(s, SafeLoader)``; aquí se usa
    una subclase de ``SafeLoader`` que solo agrega el rechazo de claves
    repetidas. Solo se construyen tipos básicos (mapeos, listas, cadenas,
    números, booleanos, fechas y ``None``) y las etiquetas que crearían objetos
    de Python se rechazan. La función no interpreta la máquina: eso es
    ``parse_machine``.
    """
    source = Path(path)
    # utf-8-sig acepta también archivos guardados con BOM; con utf-8 el texto empezaría con U+FEFF.
    try:
        text = source.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise YamlLoadError(f"{source}: no se puede leer el archivo ({error.strerror or error})") from error
    except UnicodeDecodeError as error:
        raise YamlLoadError(f"{source}: el archivo no está codificado en UTF-8 ({error.reason})") from error

    try:
        document = yaml.load(text, Loader=_UniqueKeySafeLoader)
    except (yaml.YAMLError, ValueError) as error:  # ValueError: escalares imposibles, p. ej. 2026-13-01
        raise YamlLoadError(f"{source}: YAML inválido\n{error}") from error

    if document is None:
        raise YamlLoadError(f"{source}: el archivo no contiene un documento YAML")
    if not isinstance(document, dict):
        raise YamlLoadError(
            f"{source}: la raíz del documento debe ser un mapeo (q_states, alphabet, ...), "
            f"no {type(document).__name__}"
        )
    return document

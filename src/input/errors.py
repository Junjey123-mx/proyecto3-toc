"""Errores de entrada: el archivo o la máquina descrita no se pueden simular.

Un error de entrada nunca es un rechazo de la cadena: se reporta antes de simular.
"""


class InputError(ValueError):
    """Base de los errores de carga, interpretación y validación."""


class YamlLoadError(InputError):
    """El archivo no se pudo leer o no contiene un único documento YAML con un mapeo."""

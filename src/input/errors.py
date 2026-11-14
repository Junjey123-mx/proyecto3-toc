"""Errores de entrada: el archivo o la máquina descrita no se pueden simular.

Un error de entrada nunca es un rechazo de la cadena: se reporta antes de simular.
"""


class InputError(ValueError):
    """Base de los errores de carga, interpretación y validación."""


class YamlLoadError(InputError):
    """El archivo no se pudo leer o no contiene un único documento YAML con un mapeo."""


class MachineParseError(InputError):
    """El documento no sigue la estructura o los tipos del esquema YAML del curso."""


class MachineValidationError(InputError):
    """La máquina o sus cadenas no satisfacen la definición formal.

    ``errors`` contiene un mensaje por problema, cada uno con su campo YAML.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = list(errors)
        super().__init__("la máquina no es válida:\n" + "\n".join(f"- {error}" for error in self.errors))

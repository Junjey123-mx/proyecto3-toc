"""Descripción instantánea (ID): fotografía completa de la MT en un paso."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from src.model.transition import BLANK, Symbol, Transition


@dataclass(frozen=True)
class Configuration:
    """ID_k = (estado, caché, cabezal, cinta) tras ``step_index`` transiciones.

    ``tape`` es una copia de solo lectura de las celdas no blancas
    (posición → símbolo). Toda posición ausente contiene el blanco, así que
    ``tape.get(i)`` devuelve el símbolo o ``None``. La copia se hace al construir,
    por lo que ninguna ID comparte estado mutable con la cinta de trabajo ni con
    otras IDs. ``applied`` es la regla que produjo esta ID (``None`` en ID_0).
    """

    step_index: int
    state: str
    cache: Symbol
    head: int
    tape: Mapping[int, str]
    applied: Transition | None = None

    def __post_init__(self) -> None:
        if self.step_index < 0:
            raise ValueError(f"step_index debe ser >= 0, no {self.step_index}")
        cells = {index: symbol for index, symbol in self.tape.items() if symbol is not BLANK}
        object.__setattr__(self, "tape", MappingProxyType(cells))

    @property
    def scanned(self) -> Symbol:
        """Símbolo bajo el cabezal (``None`` si es blanco)."""
        return self.tape.get(self.head)

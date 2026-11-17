"""Cinta dispersa: solo se almacenan las celdas no blancas."""

from collections.abc import Mapping
from types import MappingProxyType

from src.model.transition import BLANK, Symbol


class Tape:
    """Cinta de trabajo infinita en ambos sentidos, representada como ``dict[int, str]``.

    Toda posición ausente contiene el blanco y escribir el blanco elimina la
    celda, así que la memoria crece con las celdas no blancas, no con las
    visitadas. Las posiciones pueden ser negativas. La cinta no conoce Γ: la
    pertenencia de símbolos la garantiza la validación de la máquina.
    """

    def __init__(self, cells: Mapping[int, Symbol] | None = None) -> None:
        # Las celdas recibidas se copian sin los blancos: una posición ausente ya equivale a B.
        self._cells: dict[int, str] = {
            index: symbol for index, symbol in (cells or {}).items() if symbol is not BLANK
        }

    @classmethod
    def from_input(cls, word: str) -> "Tape":
        """Cinta inicial: ``word`` desde la posición 0 y blanco en el resto."""
        return cls(dict(enumerate(word)))

    def read(self, index: int) -> Symbol:
        """Símbolo en ``index``; ``None`` (blanco) si la celda no está almacenada."""
        return self._cells.get(index, BLANK)

    def write(self, index: int, symbol: Symbol) -> None:
        """Escribe ``symbol`` en ``index``; escribir el blanco borra la celda."""
        # Borrar en lugar de guardar None deja una sola representación del blanco.
        if symbol is BLANK:
            self._cells.pop(index, None)
        else:
            self._cells[index] = symbol

    def snapshot(self) -> Mapping[int, str]:
        """Copia de solo lectura de las celdas no blancas, independiente de esta cinta."""
        # La copia desacopla la ID de la cinta de trabajo y el proxy impide modificarla.
        return MappingProxyType(dict(self._cells))

    def __repr__(self) -> str:
        return f"Tape({self._cells!r})"

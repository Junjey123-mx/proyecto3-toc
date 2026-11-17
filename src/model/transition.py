"""Vocabulario de la función de transición δ: símbolos, blanco, movimientos y reglas."""

from dataclasses import dataclass
from enum import Enum

Symbol = str | None
"""Símbolo de cinta o valor de caché; ``None`` representa el blanco."""

BLANK: Symbol = None
"""Símbolo blanco B. El enunciado lo define como ``null``/``None`` (entrada vacía en YAML)."""


class Move(Enum):
    """Desplazamiento del cabezal; el valor es el cambio de posición."""

    L = -1
    R = 1
    S = 0


@dataclass(frozen=True)
class Transition:
    """Regla δ([state, cache], read) = ([next_state, next_cache], write, move).

    Equivale a un elemento de ``delta`` del YAML del curso:
    ``params.initial_state``, ``params.mem_cache_value`` y ``params.tape_input``
    forman la clave (``state``, ``cache``, ``read``); ``output.final_state``,
    ``output.mem_cache_value``, ``output.tape_output`` y
    ``output.tape_displacement`` forman el resultado (``next_state``,
    ``next_cache``, ``write``, ``move``).
    """

    state: str
    cache: Symbol
    read: Symbol
    next_state: str
    next_cache: Symbol
    write: Symbol
    move: Move

    def __post_init__(self) -> None:
        # El parser ya convierte L/R/S en Move; esta comprobación protege las reglas creadas desde Python.
        if not isinstance(self.move, Move):
            raise TypeError(f"move debe ser Move.L, Move.R o Move.S, no {self.move!r}")

    @property
    def key(self) -> tuple[str, Symbol, Symbol]:
        """Clave de búsqueda en δ: (estado, caché, símbolo leído)."""
        return (self.state, self.cache, self.read)

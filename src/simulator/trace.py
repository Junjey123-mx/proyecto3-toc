"""Traza de una simulación: la secuencia completa ID_0 ... ID_n lista para presentarse.

El motor ya produce IDs inmutables (``SimulationResult.configurations``). Este
módulo las convierte en entradas de traza con todo lo necesario para escribir la
tabla «Paso | ID | Transición» de los laboratorios: paso, estado, caché, cabezal,
copia de la cinta, símbolo leído y regla aplicada. Además comprueba que cada
ID_k+1 sea exactamente una aplicación de δ sobre ID_k; nunca vuelve a ejecutar
la máquina ni modifica el resultado.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from src.model.configuration import Configuration
from src.model.simulation_result import Outcome, SimulationResult
from src.model.transition import BLANK, Symbol, Transition


class TraceError(ValueError):
    """La secuencia de IDs no corresponde a aplicaciones sucesivas de δ."""


@dataclass(frozen=True)
class TraceEntry:
    """ID_k de la traza.

    ``tape`` es una copia de solo lectura de las celdas no blancas (posición →
    símbolo); cualquier otra posición contiene el blanco. ``scanned`` es el
    símbolo bajo el cabezal en esta ID y ``applied`` la regla que produjo esta
    ID a partir de la anterior (``None`` en ID_0).
    """

    step: int
    state: str
    cache: Symbol
    head: int
    tape: Mapping[int, str]
    applied: Transition | None

    def __post_init__(self) -> None:
        cells = {index: symbol for index, symbol in self.tape.items() if symbol is not BLANK}
        object.__setattr__(self, "tape", MappingProxyType(cells))

    @classmethod
    def from_configuration(cls, config: Configuration) -> "TraceEntry":
        """Copia una ``Configuration`` del motor en una entrada de traza independiente."""
        return cls(config.step_index, config.state, config.cache, config.head, dict(config.tape), config.applied)

    @property
    def scanned(self) -> Symbol:
        """Símbolo bajo el cabezal (``None`` si es blanco)."""
        return self.tape.get(self.head)

    def span(self, input_length: int) -> tuple[int, int]:
        """Rango de posiciones ``(izquierda, derecha)`` que debe mostrar la ID.

        Cubre la zona donde se escribió la entrada (``0 .. input_length - 1``),
        todas las celdas no blancas y el cabezal. Así se conservan los blancos
        que dejó la máquina sobre la entrada, como en el Laboratorio 10
        (``BBB#XXXB[q5,B]B``), y el cabezal siempre queda dentro del rango,
        aunque esté en una posición negativa o después del último símbolo.
        """
        positions = [self.head, *self.tape]
        if input_length > 0:
            positions += [0, input_length - 1]
        return min(positions), max(positions)


@dataclass(frozen=True)
class Trace:
    """Historial completo de una cadena: ``entries`` = (ID_0, ..., ID_n), sin truncar."""

    word: str
    outcome: Outcome
    reason: str
    entries: tuple[TraceEntry, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))
        if not self.entries:
            raise TraceError("una traza debe contener al menos ID_0")

    @property
    def steps(self) -> int:
        """Transiciones aplicadas (IDs - 1)."""
        return len(self.entries) - 1

    @property
    def final(self) -> TraceEntry:
        """Última ID."""
        return self.entries[-1]


def build_trace(result: SimulationResult) -> Trace:
    """Construye la traza de ``result`` y verifica que sea una computación válida.

    Comprueba que ID_0 no tenga regla aplicada, que los pasos sean 0, 1, ..., n
    y que cada ID_k+1 resulte de aplicar su regla a ID_k: la clave de la regla
    coincide con (estado, caché, símbolo leído) de ID_k, y el estado, la caché,
    el cabezal y la cinta de ID_k+1 son los que indica la regla. Lanza
    ``TraceError`` si algo no coincide. ``result`` no se modifica.
    """
    entries = tuple(TraceEntry.from_configuration(config) for config in result.configurations)
    first = entries[0]
    if first.step != 0 or first.applied is not None:
        raise TraceError("ID_0 debe tener paso 0 y ninguna regla aplicada")
    for previous, current in zip(entries, entries[1:]):
        _check_move(previous, current)
    return Trace(result.word, result.outcome, result.reason, entries)


def _check_move(previous: TraceEntry, current: TraceEntry) -> None:
    where = f"ID_{previous.step} ⊢ ID_{current.step}"
    rule = current.applied
    if current.step != previous.step + 1:
        raise TraceError(f"{where}: los pasos deben ser consecutivos")
    if rule is None:
        raise TraceError(f"{where}: falta la regla aplicada")
    if rule.key != (previous.state, previous.cache, previous.scanned):
        raise TraceError(f"{where}: la regla {rule.key!r} no corresponde a la ID anterior")
    expected_tape = dict(previous.tape)
    if rule.write is BLANK:
        expected_tape.pop(previous.head, None)
    else:
        expected_tape[previous.head] = rule.write
    expected = (rule.next_state, rule.next_cache, previous.head + rule.move.value, expected_tape)
    if (current.state, current.cache, current.head, dict(current.tape)) != expected:
        raise TraceError(f"{where}: la ID no es el resultado de aplicar la regla")

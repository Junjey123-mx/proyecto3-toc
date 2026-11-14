"""Resultado de simular una cadena: motivo de parada e historial completo de IDs."""

from dataclasses import dataclass
from enum import Enum

from src.model.configuration import Configuration


class Outcome(Enum):
    """Motivo de parada de una simulación.

    Un archivo o una máquina inválidos no producen un ``Outcome``: se reportan
    como excepciones de entrada antes de simular.
    """

    ACCEPTED = "ACCEPTED"
    """La ID alcanzó un estado de F."""
    REJECTED = "REJECTED"
    """No hay regla aplicable y el estado no pertenece a F."""
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    """Se agotó ``max_steps``; es una salvaguarda operativa, no un rechazo."""


@dataclass(frozen=True)
class SimulationResult:
    """Simulación de ``word``: ``configurations`` = (ID_0, ..., ID_n) en orden."""

    word: str
    outcome: Outcome
    configurations: tuple[Configuration, ...]
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "configurations", tuple(self.configurations))
        if not self.configurations:
            raise ValueError("un resultado debe contener al menos ID_0")

    @property
    def final(self) -> Configuration:
        """Última ID: estado, caché, cabezal y cinta al detenerse."""
        return self.configurations[-1]

    @property
    def steps(self) -> int:
        """Cantidad de transiciones aplicadas (IDs - 1)."""
        return len(self.configurations) - 1

"""Descripción formal M = (Q, Σ, Γ, δ, q0, B, F) de una MT de una cinta con caché."""

from dataclasses import dataclass

from src.model.transition import Symbol, Transition


@dataclass(frozen=True)
class TuringMachine:
    """MT determinista de una cinta cuya unidad de control almacena un valor de caché.

    ``states`` es Q, ``input_alphabet`` es Σ, ``tape_alphabet`` es Γ (incluye el
    blanco ``None``), ``final_states`` es F y ``transitions`` conserva δ en el
    orden del YAML. Los conjuntos se normalizan a ``frozenset`` y δ a ``tuple``;
    ``final_states`` acepta también un único estado, como ``final: '5'`` del
    enunciado. La coherencia entre componentes la verifica ``validate_machine``.
    """

    states: frozenset[str]
    input_alphabet: frozenset[str]
    tape_alphabet: frozenset[Symbol]
    initial_state: str
    final_states: frozenset[str]
    transitions: tuple[Transition, ...]

    def __post_init__(self) -> None:
        for name in ("states", "input_alphabet", "tape_alphabet"):
            object.__setattr__(self, name, frozenset(getattr(self, name)))
        final = self.final_states
        object.__setattr__(self, "final_states", frozenset([final] if isinstance(final, str) else final))
        object.__setattr__(self, "transitions", tuple(self.transitions))

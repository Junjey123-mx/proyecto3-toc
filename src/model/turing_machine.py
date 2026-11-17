"""Descripción formal M = (Q, Σ, Γ, δ, q0, B, F) de una MT de una cinta con caché."""

from dataclasses import dataclass, field

from src.model.transition import Symbol, Transition


@dataclass(frozen=True)
class TuringMachine:
    """MT determinista de una cinta cuya unidad de control almacena un valor de caché.

    ``states`` es Q, ``input_alphabet`` es Σ, ``tape_alphabet`` es Γ (incluye el
    blanco ``None``), ``final_states`` es F y ``transitions`` conserva δ en el
    orden del YAML. Los conjuntos se normalizan a ``frozenset`` y δ a ``tuple``;
    ``final_states`` acepta también un único estado, como ``final: '5'`` del
    enunciado. La coherencia entre componentes la verifica ``validate_machine``.

    δ se indexa por (estado, caché, símbolo leído). Dos reglas con la misma clave,
    idénticas o no, hacen que δ no sea una función: la construcción falla con
    ``ValueError`` indicando sus posiciones en ``transitions``.
    """

    states: frozenset[str]
    input_alphabet: frozenset[str]
    tape_alphabet: frozenset[Symbol]
    initial_state: str
    final_states: frozenset[str]
    transitions: tuple[Transition, ...]
    _index: dict[tuple[str, Symbol, Symbol], Transition] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        # La dataclass es frozen: object.__setattr__ es la única forma de normalizar los campos al crearla.
        for name in ("states", "input_alphabet", "tape_alphabet"):
            object.__setattr__(self, name, frozenset(getattr(self, name)))
        final = self.final_states
        object.__setattr__(self, "final_states", frozenset([final] if isinstance(final, str) else final))
        object.__setattr__(self, "transitions", tuple(self.transitions))

        # δ se indexa una sola vez: cada paso de la simulación la consulta en O(1) esperado.
        index: dict[tuple[str, Symbol, Symbol], Transition] = {}
        for position, rule in enumerate(self.transitions):
            first = index.get(rule.key)
            # Una segunda regla con la misma clave haría que δ no fuera una función (no determinismo).
            if first is not None:
                kind = "duplicadas" if first == rule else "en conflicto"
                raise ValueError(
                    f"δ no es determinista: las reglas {self.transitions.index(first)} y "
                    f"{position} están {kind} para (estado, caché, lectura) = {rule.key!r}"
                )
            index[rule.key] = rule
        object.__setattr__(self, "_index", index)

    def find_transition(self, state: str, cache: Symbol, symbol: Symbol) -> Transition | None:
        """Regla δ([state, cache], symbol) o ``None`` si no está definida (la MT se detiene)."""
        return self._index.get((state, cache, symbol))

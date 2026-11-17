"""Convierte el documento YAML del curso en un ``TuringMachine`` y sus cadenas de prueba."""

from collections.abc import Mapping
from typing import Any

from src.input.errors import MachineParseError
from src.model.transition import Move, Symbol, Transition
from src.model.turing_machine import TuringMachine

_QUOTE_HINT = "; en YAML escríbalo entre comillas (p. ej. '0') para que sea una cadena"


def parse_machine(document: Mapping[str, Any]) -> tuple[TuringMachine, list[str]]:
    """Traduce el esquema del enunciado a objetos del modelo.

    Comprueba estructura y tipos: claves obligatorias, listas, cadenas no
    vacías, blanco (``None``) solo donde el contrato lo admite, movimientos
    ``L``/``R``/``S``, elementos repetidos y reglas δ con la misma clave. Los
    nombres de estados y símbolos se conservan tal cual (``'0'`` sigue siendo
    ``'0'``). La coherencia entre componentes (estados declarados, Σ ⊆ Γ,
    símbolos de las cadenas) la comprueba ``validate_machine``.

    Devuelve la máquina y ``simulation_strings`` en el orden del archivo.
    Lanza ``MachineParseError`` con la ruta del campo, p. ej.
    ``delta[3].output.tape_displacement``.
    """
    root = _mapping(document, "raíz")
    q_states = _mapping(_require(root, "q_states", "raíz"), "q_states")
    states = _texts(_require(q_states, "q_list", "q_states"), "q_states.q_list")
    initial = _field(q_states, "initial", "q_states")
    # final admite un solo estado, como ``final: '5'`` del enunciado, o una lista de estados.
    final = _require(q_states, "final", "q_states")
    finals = _texts(final, "q_states.final") if isinstance(final, list) else [_text(final, "q_states.final")]
    alphabet = _texts(_require(root, "alphabet", "raíz"), "alphabet")
    # Γ es el único conjunto que puede contener el blanco, escrito como una entrada vacía.
    tape_alphabet = _texts(_require(root, "tape_alphabet", "raíz"), "tape_alphabet", blank=True)
    transitions = [
        _transition(entry, f"delta[{index}]")
        for index, entry in enumerate(_list(_require(root, "delta", "raíz"), "delta"))
    ]
    strings = [
        _input_string(value, f"simulation_strings[{index}]")
        for index, value in enumerate(_list(_require(root, "simulation_strings", "raíz"), "simulation_strings"))
    ]
    # TuringMachine detecta dos reglas con la misma clave; el error se reporta como un problema de delta.
    try:
        machine = TuringMachine(states, alphabet, tape_alphabet, initial, finals, transitions)
    except ValueError as error:
        raise MachineParseError(f"delta: {error}") from error
    return machine, strings


def _transition(entry: Any, where: str) -> Transition:
    """Una regla de ``delta``: ``params`` forma la clave de δ y ``output`` su resultado."""
    rule = _mapping(entry, where)
    params = _mapping(_require(rule, "params", where), f"{where}.params")
    output = _mapping(_require(rule, "output", where), f"{where}.output")
    move = _require(output, "tape_displacement", f"{where}.output")
    # Se valida antes de Move[move] para que el error indique la ruta del campo.
    if move not in ("L", "R", "S"):
        raise MachineParseError(f"{where}.output.tape_displacement: debe ser L, R o S, no {move!r}")
    # El blanco se admite en la caché, en la lectura y en la escritura, pero nunca como estado.
    return Transition(
        state=_field(params, "initial_state", f"{where}.params"),
        cache=_field(params, "mem_cache_value", f"{where}.params", blank=True),
        read=_field(params, "tape_input", f"{where}.params", blank=True),
        next_state=_field(output, "final_state", f"{where}.output"),
        next_cache=_field(output, "mem_cache_value", f"{where}.output", blank=True),
        write=_field(output, "tape_output", f"{where}.output", blank=True),
        move=Move[move],
    )


def _input_string(value: Any, where: str) -> str:
    """Una cadena de ``simulation_strings``; un valor que YAML no leyó como texto se rechaza con una sugerencia."""
    if isinstance(value, str):
        return value
    hint = "; la cadena vacía se escribe ''" if value is None else _hint(value)
    raise MachineParseError(f"{where}: se esperaba una cadena, no {value!r}{hint}")


def _require(mapping: Mapping[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise MachineParseError(f"{where}: falta la clave obligatoria '{key}'")
    return mapping[key]


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MachineParseError(f"{where}: se esperaba un mapeo, no {value!r}")
    return value


def _list(value: Any, where: str) -> list[Any]:
    if not isinstance(value, list):
        raise MachineParseError(f"{where}: se esperaba una lista, no {value!r}")
    return value


def _field(mapping: Mapping[str, Any], key: str, where: str, *, blank: bool = False) -> Symbol:
    """Campo obligatorio ``key`` como texto, con su ruta completa en los mensajes de error."""
    return _text(_require(mapping, key, where), f"{where}.{key}", blank=blank)


def _text(value: Any, where: str, *, blank: bool = False) -> Symbol:
    """Cadena no vacía; el blanco (``None``) solo si ``blank``."""
    if value is None:
        if blank:
            return None
        raise MachineParseError(f"{where}: el blanco (entrada vacía) no está permitido aquí")
    if isinstance(value, str) and value:
        return value
    raise MachineParseError(f"{where}: se esperaba una cadena no vacía, no {value!r}{_hint(value)}")


def _texts(value: Any, where: str, *, blank: bool = False) -> list[Symbol]:
    """Lista de textos sin repetidos: Q, Σ, Γ o F declarados como conjuntos."""
    items = [_text(item, f"{where}[{index}]", blank=blank) for index, item in enumerate(_list(value, where))]
    repeated = sorted({repr(item) for item in items if items.count(item) > 1})
    if repeated:
        raise MachineParseError(f"{where}: elementos repetidos: {', '.join(repeated)}")
    return items


def _hint(value: Any) -> str:
    """Sugiere comillas cuando YAML convirtió el valor en número o booleano (``0101`` se lee como 65)."""
    return _QUOTE_HINT if isinstance(value, (bool, int, float)) else ""

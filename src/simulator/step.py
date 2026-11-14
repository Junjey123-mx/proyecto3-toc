"""Transición atómica: ID_k ⊢ ID_k+1."""

from src.model.configuration import Configuration
from src.model.tape import Tape
from src.model.turing_machine import TuringMachine


def step(machine: TuringMachine, current: Configuration) -> Configuration | None:
    """Aplica exactamente una regla de δ a ``current`` y devuelve la ID siguiente.

    1. Lee el símbolo bajo el cabezal.
    2. Busca δ([estado, caché], símbolo).
    3. Escribe el símbolo de salida (escribir el blanco borra la celda).
    4. Cambia el estado y la caché.
    5. Desplaza el cabezal (L = -1, R = +1, S = 0).
    6. Construye una ID nueva con ``step_index + 1`` y la regla aplicada.

    Devuelve ``None`` si no hay regla. ``current`` nunca se modifica. La función
    no decide la parada: aceptar en F o limitar pasos corresponde a ``simulate``.
    """
    rule = machine.find_transition(current.state, current.cache, current.scanned)
    if rule is None:
        return None
    tape = Tape(current.tape)
    tape.write(current.head, rule.write)
    return Configuration(
        step_index=current.step_index + 1,
        state=rule.next_state,
        cache=rule.next_cache,
        head=current.head + rule.move.value,
        tape=tape.snapshot(),
        applied=rule,
    )

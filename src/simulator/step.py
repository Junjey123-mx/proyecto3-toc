"""Transición atómica: ID_k ⊢ ID_k+1."""

from src.model.configuration import Configuration
from src.model.tape import Tape
from src.model.turing_machine import TuringMachine


def step(machine: TuringMachine, current: Configuration) -> Configuration | None:
    """Aplica exactamente una regla de δ a ``current`` y devuelve la ID siguiente.

    Implementa los pasos 1 a 8 del procedimiento mecanizado:

    1. Parte de la configuración actual ID_k = ``current``.
    2. Toma su estado q, su caché c y el símbolo X bajo el cabezal.
    3. Busca la regla δ([q, c], X).
    4. Escribe el símbolo de salida (escribir el blanco borra la celda).
    5–6. Cambia el estado y la caché por los de la regla.
    7. Desplaza el cabezal (L = -1, R = +1, S = 0).
    8. Construye una ID nueva con ``step_index + 1`` y la regla aplicada.

    Devuelve ``None`` si no hay regla. ``current`` nunca se modifica. La función
    no decide la parada: registrar la ID (paso 9), aceptar en F o limitar los
    pasos (paso 10) corresponde a ``simulate``.
    """
    # Pasos 2 y 3: la clave de δ es (estado, caché, símbolo leído); a lo sumo hay una regla.
    rule = machine.find_transition(current.state, current.cache, current.scanned)
    # Sin regla la MT se detiene; si eso es aceptación o rechazo lo decide simulate.
    if rule is None:
        return None
    # Paso 4: se escribe sobre una copia, así ID_k conserva la cinta que tenía.
    tape = Tape(current.tape)
    tape.write(current.head, rule.write)
    # Pasos 5 a 8: estado y caché de la regla, cabezal desplazado y cinta congelada.
    # Un movimiento L desde la posición 0 lleva el cabezal a -1, que la cinta admite.
    return Configuration(
        step_index=current.step_index + 1,
        state=rule.next_state,
        cache=rule.next_cache,
        head=current.head + rule.move.value,
        tape=tape.snapshot(),
        applied=rule,
    )

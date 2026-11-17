"""Motor de simulación: ID_0, transiciones sucesivas y condición de parada."""

from src.model.configuration import Configuration
from src.model.simulation_result import Outcome, SimulationResult
from src.model.tape import Tape
from src.model.transition import BLANK, Symbol
from src.model.turing_machine import TuringMachine
from src.simulator.step import step

DEFAULT_MAX_STEPS = 10_000
"""Cota operativa de transiciones; la parada no es decidible en general."""


def simulate(machine: TuringMachine, word: str, max_steps: int = DEFAULT_MAX_STEPS) -> SimulationResult:
    """Simula ``word`` desde ID_0 = [q0, B] w y conserva todas las IDs.

    ID_0 tiene el estado inicial, la caché en blanco, el cabezal en la posición 0
    (primer símbolo de ``word``, o blanco si es vacía) y ``word`` en la cinta.
    Antes de cada transición se comprueba, en este orden:

    1. estado ∈ F → ``ACCEPTED`` (los estados finales son terminales);
    2. no hay regla aplicable → ``REJECTED``;
    3. ya se aplicaron ``max_steps`` transiciones → ``LIMIT_EXCEEDED``.

    Así, ``LIMIT_EXCEEDED`` solo ocurre si la máquina aún podía continuar: una
    MT que se detiene (en F o sin regla) justo tras ``max_steps`` transiciones
    se acepta o se rechaza normalmente. Cada llamada parte de una configuración
    nueva, por lo que las simulaciones no comparten estado. Lanza
    ``ValueError`` si ``max_steps`` < 1 o si ``word`` usa símbolos fuera de Σ.
    """
    if max_steps < 1:
        raise ValueError(f"max_steps debe ser un entero positivo, no {max_steps!r}")
    # Una cadena fuera de Σ* es un error de entrada, no un rechazo: se informa antes de crear ID_0.
    outside = sorted(set(word) - machine.input_alphabet)
    if outside:
        raise ValueError(f"la cadena {word!r} usa símbolos fuera del alfabeto de entrada: {outside}")

    # ID_0 = [q0, B] w: estado inicial, caché en blanco, cabezal en 0 y w escrita desde esa posición.
    current = Configuration(0, machine.initial_state, BLANK, 0, Tape.from_input(word).snapshot())
    # Paso 9: el historial registra cada ID; son inmutables, así que ninguna cambia después.
    history = [current]
    # Paso 10: los estados de F son terminales y se comprueban antes de buscar otra regla.
    while current.state not in machine.final_states:
        following = step(machine, current)
        # El paso se calcula antes de revisar el límite: una MT sin regla se rechaza aunque
        # haya agotado max_steps.
        if following is None:
            reason = (
                f"no hay regla para el estado {current.state!r} con caché {_show(current.cache)} "
                f"leyendo {_show(current.scanned)}, y {current.state!r} no es final"
            )
            return SimulationResult(word, Outcome.REJECTED, history, reason)
        # Aún había una regla aplicable: la ID calculada se descarta y la traza termina con
        # exactamente max_steps transiciones, sin veredicto de aceptación ni de rechazo.
        if current.step_index >= max_steps:
            reason = f"se aplicaron {max_steps} transiciones y la máquina aún no se detiene"
            return SimulationResult(word, Outcome.LIMIT_EXCEEDED, history, reason)
        history.append(following)
        current = following
    return SimulationResult(word, Outcome.ACCEPTED, history, f"alcanzó el estado final {current.state!r}")


def _show(symbol: Symbol) -> str:
    """Símbolo para el motivo de parada: «el blanco» o el símbolo entre comillas."""
    return "el blanco" if symbol is BLANK else repr(symbol)

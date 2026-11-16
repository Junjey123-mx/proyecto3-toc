"""Presentación de una ejecución en el menú: entrada, procedimiento, configuración final y veredicto.

Solo da formato a una ``Trace`` que ya calculó el motor; no simula ni deduce
resultados. Las IDs con sus reglas y la configuración final son las mismas
líneas que imprime ``--machine`` (``format_procedure`` y
``format_final_configuration``); aquí se ordenan en bloques delimitados para que
el veredicto aparezca al final, después del procedimiento completo.
"""

from src.model.simulation_result import Outcome
from src.output.result_formatter import BLANK_TAPE, format_final_configuration, format_procedure, show_word
from src.output.tape_formatter import tape_contents
from src.simulator.trace import Trace

WIDTH = 49
MAJOR = "=" * WIDTH
MINOR = "-" * WIDTH
VERDICTS = {
    (Outcome.ACCEPTED, True): "CADENA ACEPTADA",
    (Outcome.REJECTED, True): "CADENA RECHAZADA",
    (Outcome.ACCEPTED, False): "TRANSFORMACIÓN COMPLETADA",
    (Outcome.REJECTED, False): "PROCESAMIENTO RECHAZADO",
    (Outcome.LIMIT_EXCEEDED, True): "LÍMITE DE PASOS ALCANZADO",
    (Outcome.LIMIT_EXCEEDED, False): "LÍMITE DE PASOS ALCANZADO",
}
"""Titular del veredicto según (resultado, ¿es reconocedora?)."""
LIMIT_NOTE = [
    "No se ha demostrado aceptación ni rechazo: la máquina aún tenía una",
    "transición aplicable. El límite de pasos no es un rechazo formal.",
]


def heading(title: str, rule: str) -> list[str]:
    return [rule, title.center(WIDTH).rstrip(), rule]


def format_verdict(trace: Trace, recognizer: bool, blank: str) -> list[str]:
    """Veredicto del motor: titular, cadena (y cinta resultante si transformó), pasos y motivo real."""
    outcome = trace.outcome
    if outcome is Outcome.ACCEPTED and not recognizer:
        result = tape_contents(trace.final.tape, blank)
        facts = [
            f"Cadena original:  {show_word(trace.word)}",
            f"Cinta resultante: {show_word(result) if result else BLANK_TAPE}",
        ]
    else:
        facts = [f"Cadena evaluada:  {show_word(trace.word)}"]
    reason = [f"{trace.reason[0].upper()}{trace.reason[1:]}."]
    if outcome is Outcome.LIMIT_EXCEEDED:
        reason += LIMIT_NOTE
    return [
        *heading("VEREDICTO FINAL", MAJOR),
        "",
        f"{outcome.value} — {VERDICTS[outcome, recognizer]}".center(WIDTH).rstrip(),
        "",
        *facts,
        f"Pasos realizados: {trace.steps}",
        "",
        "Motivo:",
        *reason,
    ]


def format_simulation(trace: Trace, machine: str, recognizer: bool, blank: str) -> list[str]:
    """Ejecución completa, en orden: inicio, todas las IDs, configuración final, veredicto y fin."""
    return [
        *heading("INICIO DE SIMULACIÓN", MAJOR),
        "",
        f"Máquina: {machine}",
        f"Cadena de entrada: {show_word(trace.word)}",
        f"Longitud: {len(trace.word)}",
        "",
        *heading("PROCEDIMIENTO PASO A PASO", MINOR),
        "",
        *format_procedure(trace, blank),
        "",
        *heading("CONFIGURACIÓN FINAL", MINOR),
        "",
        *format_final_configuration(trace, blank),
        "",
        *format_verdict(trace, recognizer, blank),
        "",
        *heading("FIN DE SIMULACIÓN", MAJOR),
    ]

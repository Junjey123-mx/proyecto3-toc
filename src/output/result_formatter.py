"""Reporte de la simulación de cada cadena y resumen de todas las cadenas de un archivo.

Funciones puras sobre ``Trace``: no simulan ni modifican la traza. El motivo de
parada se muestra con el valor exacto de ``Outcome`` (``ACCEPTED``,
``REJECTED`` o ``LIMIT_EXCEEDED``) para que cada resultado se identifique sin
interpretar el texto; ``LIMIT_EXCEEDED`` nunca se presenta como rechazo.
"""

from collections.abc import Sequence

from src.model.simulation_result import Outcome
from src.output.id_formatter import format_id, format_id_lines
from src.output.tape_formatter import render_entry_tape, tape_contents
from src.simulator.trace import Trace
from src.utils.notation import DEFAULT_BLANK_GLYPH, show_symbol

OUTCOME_LABELS = {
    Outcome.ACCEPTED: "aceptada",
    Outcome.REJECTED: "rechazada",
    Outcome.LIMIT_EXCEEDED: "sin veredicto: se alcanzó el límite de pasos, no es un rechazo",
}

EMPTY_WORD = "ε (cadena vacía)"
BLANK_TAPE = "(cinta en blanco)"


def show_word(word: str) -> str:
    """Cadena entre comillas, o ``ε`` si es vacía."""
    return f"'{word}'" if word else EMPTY_WORD


def format_outcome(outcome: Outcome) -> str:
    """``ACCEPTED (aceptada)``, ``REJECTED (rechazada)`` o ``LIMIT_EXCEEDED (sin veredicto: ...)``."""
    return f"{outcome.value} ({OUTCOME_LABELS[outcome]})"


def format_result(
    trace: Trace,
    number: int | None = None,
    total: int | None = None,
    blank: str = DEFAULT_BLANK_GLYPH,
    max_tape_cells: int | None = None,
) -> list[str]:
    """Reporte de una cadena: encabezado, veredicto, cinta final y la tabla completa de IDs.

    ``number``/``total`` numeran la cadena dentro del archivo. «Cinta final»
    es el contenido de la cinta desde la primera hasta la última celda no
    blanca (la salida de una máquina alteradora). ``max_tape_cells`` solo
    condensa la vista por posiciones de la cinta final; la tabla de IDs se
    muestra siempre completa.
    """
    position = f"Cadena {number} de {total}: " if number is not None and total is not None else "Cadena: "
    return [
        f"=== {position}{show_word(trace.word)} (longitud {len(trace.word)}) ===",
        f"Resultado:     {format_outcome(trace.outcome)}",
        f"Motivo:        {trace.reason}",
        f"Pasos:         {trace.steps}",
        *format_final_configuration(trace, blank, max_tape_cells),
        "",
        *format_procedure(trace, blank),
    ]


def format_final_configuration(
    trace: Trace, blank: str = DEFAULT_BLANK_GLYPH, max_tape_cells: int | None = None
) -> list[str]:
    """Estado, caché, cabezal, cinta e ID de la última configuración, y la cinta por posiciones."""
    final = trace.final
    length = len(trace.word)
    return [
        f"Estado final:  {final.state}",
        f"Caché final:   {show_symbol(final.cache, blank)}",
        f"Cabezal final: {final.head}",
        f"Cinta final:   {tape_contents(final.tape, blank) or BLANK_TAPE}",
        f"ID final:      {format_id(final, length, blank)}",
        "",
        *render_entry_tape(final, length, blank, max_tape_cells),
    ]


def format_procedure(trace: Trace, blank: str = DEFAULT_BLANK_GLYPH) -> list[str]:
    """Todas las IDs, de ID_0 a ID_n, cada una con la regla δ que la produjo."""
    return [
        f"Descripciones instantáneas (ID_0 a ID_{trace.steps}):",
        *(f"  {line}" for line in format_id_lines(trace, blank)),
    ]


def format_summary(traces: Sequence[Trace], blank: str = DEFAULT_BLANK_GLYPH) -> list[str]:
    """Tabla con una fila por cadena: número, cadena, longitud, resultado, pasos y cinta final."""
    header = ("#", "Cadena", "Longitud", "Resultado", "Pasos", "Cinta final")
    rows = [
        (
            str(number),
            trace.word or "ε",
            str(len(trace.word)),
            trace.outcome.value,
            str(trace.steps),
            tape_contents(trace.final.tape, blank) or BLANK_TAPE,
        )
        for number, trace in enumerate(traces, start=1)
    ]
    widths = [max(len(row[column]) for row in (header, *rows)) for column in range(len(header))]
    return [
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip()
        for row in (header, *rows)
    ]

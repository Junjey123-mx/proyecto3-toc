"""Descripciones instantáneas en la notación del curso: X1…Xi-1 [q, c] Xi…Xn.

Funciones puras: reciben entradas de traza y devuelven texto, sin modificar la
traza ni ejecutar transiciones.
"""

from src.simulator.trace import Trace, TraceEntry
from src.utils.notation import DEFAULT_BLANK_GLYPH, format_control, format_rule, show_symbol

NO_RULE = "—"
"""Texto de la columna de transición para ID_0, que no proviene de ninguna regla."""


def format_id(entry: TraceEntry, input_length: int, blank: str = DEFAULT_BLANK_GLYPH) -> str:
    """ID completa: la tupla ``[estado,caché]`` se inserta antes del símbolo bajo el cabezal.

    El rango mostrado es ``entry.span(input_length)``: la zona de la entrada,
    las celdas no blancas y el cabezal, sin truncar. Los blancos dentro del rango
    se escriben con ``blank``; si el cabezal está sobre un blanco fuera del
    contenido, ese blanco también se muestra (``ab[q1,B]B``) para que el
    movimiento sea comprensible.
    """
    left, right = entry.span(input_length)
    control = format_control(entry.state, entry.cache, blank)
    cells = []
    for position in range(left, right + 1):
        # La tupla [q, c] va justo antes de la celda bajo el cabezal: X1…Xi-1 [q, c] Xi…Xn.
        if position == entry.head:
            cells.append(control)
        cells.append(show_symbol(entry.tape.get(position), blank))
    return "".join(cells)


def format_id_lines(trace: Trace, blank: str = DEFAULT_BLANK_GLYPH) -> list[str]:
    """Tabla «Paso | ID | Transición aplicada» con una fila por ID, de ID_0 a ID_n.

    Cada fila k > 0 muestra la regla que transformó ID_k-1 en ID_k, de modo que
    cualquier paso se puede reconstruir a mano a partir de la fila anterior.
    """
    length = len(trace.word)
    ids = [format_id(entry, length, blank) for entry in trace.entries]
    rules = [NO_RULE if entry.applied is None else format_rule(entry.applied, blank) for entry in trace.entries]
    # Los anchos salen de todas las filas: la tabla se alinea sin recortar ninguna ID.
    step_width = max(len("Paso"), len(str(trace.steps)))
    id_width = max(len("ID"), *(len(text) for text in ids))
    lines = [f"{'Paso':>{step_width}}  {'ID':<{id_width}}  Transición aplicada"]
    lines += [
        f"{entry.step:>{step_width}}  {text:<{id_width}}  {rule}"
        for entry, text, rule in zip(trace.entries, ids, rules)
    ]
    return lines

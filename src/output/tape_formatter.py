"""Representación textual de la cinta: contenido lógico y vista por posiciones con el cabezal.

Funciones puras, sin colores ANSI: el texto es UTF-8 plano y se puede copiar o
redirigir a un archivo. La vista por posiciones admite un modo condensado
(``max_cells``) solo para visualización; las IDs completas las produce
``id_formatter`` y nunca se recortan.
"""

from collections.abc import Mapping

from src.simulator.trace import TraceEntry
from src.utils.notation import DEFAULT_BLANK_GLYPH, show_symbol

HEAD_MARK = "^"
ELLIPSIS = "…"
_LABELS = ("posición", "cinta", "cabezal")


def tape_contents(tape: Mapping[int, str], blank: str = DEFAULT_BLANK_GLYPH) -> str:
    """Contenido de la cinta desde la primera hasta la última celda no blanca.

    Es la salida de una MT alteradora: los blancos de los extremos no forman
    parte del resultado, pero un blanco entre dos símbolos sí se muestra (con
    ``blank``) para no ocultar un error de la máquina. Una cinta en blanco
    devuelve ``""``.
    """
    if not tape:
        return ""
    return "".join(show_symbol(tape.get(i), blank) for i in range(min(tape), max(tape) + 1))


def render_tape(
    tape: Mapping[int, str],
    head: int,
    left: int,
    right: int,
    blank: str = DEFAULT_BLANK_GLYPH,
    max_cells: int | None = None,
) -> list[str]:
    """Tres líneas alineadas: posiciones ``left..right``, símbolos y marca ``^`` del cabezal.

    ``left``/``right`` se amplían, si hace falta, para incluir el cabezal. Con
    ``max_cells`` la vista se limita a esa cantidad de celdas alrededor del
    cabezal y los extremos omitidos se indican con ``…``; sin él se muestran
    todas las posiciones del rango.
    """
    if max_cells is not None and max_cells < 1:
        raise ValueError(f"max_cells debe ser positivo, no {max_cells!r}")
    left, right = min(left, head), max(right, head)
    if max_cells is not None and right - left + 1 > max_cells:
        start = min(max(left, head - max_cells // 2), right - max_cells + 1)
        cut_left, cut_right = start > left, start + max_cells - 1 < right
        left, right = start, start + max_cells - 1
    else:
        cut_left = cut_right = False

    positions = list(range(left, right + 1))
    width = max(len(str(p)) for p in positions)
    columns = [(str(p), show_symbol(tape.get(p), blank), HEAD_MARK if p == head else "") for p in positions]
    if cut_left:
        columns.insert(0, (ELLIPSIS, ELLIPSIS, ""))
    if cut_right:
        columns.append((ELLIPSIS, ELLIPSIS, ""))

    label_width = max(len(label) for label in _LABELS)
    return [
        (f"{label:<{label_width}} " + " ".join(f"{column[row]:>{width}}" for column in columns)).rstrip()
        for row, label in enumerate(_LABELS)
    ]


def render_entry_tape(
    entry: TraceEntry, input_length: int, blank: str = DEFAULT_BLANK_GLYPH, max_cells: int | None = None
) -> list[str]:
    """``render_tape`` sobre el rango visible de una ID (``entry.span(input_length)``)."""
    left, right = entry.span(input_length)
    return render_tape(entry.tape, entry.head, left, right, blank, max_cells)

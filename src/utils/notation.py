"""Notación textual del curso para símbolos, tuplas de control y reglas de δ."""

from itertools import chain, count

from src.model.transition import BLANK, Symbol, Transition
from src.model.turing_machine import TuringMachine

DEFAULT_BLANK_GLYPH = "B"
"""Representación del blanco en las IDs, como en los laboratorios (``BBB#XXXB[q5,B]B``)."""

FALLBACK_BLANK_GLYPH = "□"
"""Primera alternativa si ``B`` es un símbolo ordinario de la máquina; le siguen ``▢``, ``▣``, …"""


def blank_glyph(machine: TuringMachine) -> str:
    """Carácter con el que se mostrará el blanco para ``machine``.

    Es ``B`` salvo que ``B`` aparezca en Γ o como valor de caché de alguna regla;
    en ese caso es el primer carácter desde ``□`` (U+25A1) que la máquina no use,
    para que el blanco nunca se confunda con un símbolo de la cinta o de la caché.
    """
    used = set(machine.tape_alphabet)
    for rule in machine.transitions:
        used.update((rule.cache, rule.next_cache))
    candidates = chain([DEFAULT_BLANK_GLYPH], map(chr, count(ord(FALLBACK_BLANK_GLYPH))))
    return next(glyph for glyph in candidates if glyph not in used)


def show_symbol(symbol: Symbol, blank: str = DEFAULT_BLANK_GLYPH) -> str:
    """Símbolo de cinta o valor de caché; el blanco (``None``) se muestra como ``blank``."""
    return blank if symbol is BLANK else symbol


def format_control(state: str, cache: Symbol, blank: str = DEFAULT_BLANK_GLYPH, *, compact: bool = True) -> str:
    """Tupla de control ``[q, c]``; ``compact`` la escribe sin espacio (``[q0,B]``) como en las IDs."""
    separator = "," if compact else ", "
    return f"[{state}{separator}{show_symbol(cache, blank)}]"


def format_rule(rule: Transition, blank: str = DEFAULT_BLANK_GLYPH) -> str:
    """Regla en la notación del enunciado: ``δ([q0, B], a) = ([q1, a], B, R)``."""
    source = format_control(rule.state, rule.cache, blank, compact=False)
    target = format_control(rule.next_state, rule.next_cache, blank, compact=False)
    return (
        f"δ({source}, {show_symbol(rule.read, blank)}) = "
        f"({target}, {show_symbol(rule.write, blank)}, {rule.move.name})"
    )

"""Descripción formal de una máquina: M = (Q, Σ, Γ, δ, q0, B, F), valores de caché y tabla δ.

Funciones puras sobre ``TuringMachine``: la CLI las usa para la cabecera de su
salida y el menú interactivo para la ficha técnica de cada máquina. Todo se
extrae de la máquina cargada desde el YAML; nada se escribe a mano.
"""

from collections.abc import Iterable

from src.model.transition import BLANK, Symbol
from src.model.turing_machine import TuringMachine
from src.utils.notation import DEFAULT_BLANK_GLYPH, format_rule, show_symbol


def format_symbols(values: Iterable[Symbol], blank: str = DEFAULT_BLANK_GLYPH) -> str:
    """Conjunto ordenado entre llaves, con el blanco al final: ``{0, 1, B}``."""
    ordered = sorted(set(values), key=lambda s: (s is BLANK, s or ""))
    return "{" + ", ".join(show_symbol(s, blank) for s in ordered) + "}"


def formal_components(machine: TuringMachine, blank: str = DEFAULT_BLANK_GLYPH) -> list[str]:
    """Q, Σ, Γ, q0, F y el blanco, una línea por componente."""
    return [
        f"Q  = {{{', '.join(sorted(machine.states))}}}",
        f"Σ  = {format_symbols(machine.input_alphabet, blank)}",
        f"Γ  = {format_symbols(machine.tape_alphabet, blank)}",
        f"q0 = {machine.initial_state}",
        f"F  = {{{', '.join(sorted(machine.final_states))}}}",
        f"B  = {blank} (blanco)",
    ]


def describe_machine(machine: TuringMachine, blank: str = DEFAULT_BLANK_GLYPH) -> list[str]:
    """Resumen formal M = (Q, Σ, Γ, δ, q0, B, F) con la tabla δ completa, en el orden del YAML."""
    width = len(str(len(machine.transitions)))
    return [
        *formal_components(machine, blank),
        f"δ  = {len(machine.transitions)} reglas" + (", en el orden del YAML:" if machine.transitions else ""),
        *(f"  {number:>{width}}. {format_rule(rule, blank)}" for number, rule in enumerate(machine.transitions, start=1)),
    ]


def cache_values(machine: TuringMachine) -> frozenset[Symbol]:
    """Valores de caché que aparecen en δ (leídos o escritos), más el blanco inicial."""
    return frozenset({BLANK, *(value for rule in machine.transitions for value in (rule.cache, rule.next_cache))})


def format_delta_table(machine: TuringMachine, blank: str = DEFAULT_BLANK_GLYPH) -> list[str]:
    """δ como tabla de columnas: número, clave (estado, caché, lectura) y resultado de cada regla."""
    header = ("#", "Estado", "Caché", "Lee", "Estado sig.", "Caché sig.", "Escribe", "Mov")
    rows = [
        (
            str(number),
            rule.state,
            show_symbol(rule.cache, blank),
            show_symbol(rule.read, blank),
            rule.next_state,
            show_symbol(rule.next_cache, blank),
            show_symbol(rule.write, blank),
            rule.move.name,
        )
        for number, rule in enumerate(machine.transitions, start=1)
    ]
    widths = [max(len(row[column]) for row in (header, *rows)) for column in range(len(header))]
    return ["  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip() for row in (header, *rows)]

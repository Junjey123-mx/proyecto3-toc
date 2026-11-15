"""Simulador de máquinas de Turing de una cinta definidas en YAML.

Uso:
    python main.py --machine machines/<archivo>.yaml [--max-steps N]

Lee la máquina y su lista ``simulation_strings``, simula cada cadena en orden y
escribe en la salida estándar la descripción formal de la máquina (con la tabla δ
completa), el reporte de cada cadena (veredicto, cinta final y todas las IDs) y
un resumen. Los errores del archivo se escriben en la salida de errores.

Códigos de salida: 0 si todas las cadenas se simularon (aceptadas, rechazadas o
detenidas por el límite de pasos), 1 si el archivo no se pudo cargar o la
máquina no es válida, 2 si los argumentos son incorrectos.
"""

import argparse
import sys
from collections.abc import Sequence
from typing import TextIO

from src.input.errors import InputError
from src.input.machine_parser import parse_machine
from src.input.machine_validator import validate_machine
from src.input.yaml_loader import load_yaml
from src.model.transition import BLANK
from src.model.turing_machine import TuringMachine
from src.output.result_formatter import format_result, format_summary
from src.simulator.engine import DEFAULT_MAX_STEPS, simulate
from src.simulator.trace import build_trace
from src.utils.notation import blank_glyph, format_rule, show_symbol

EXIT_OK = 0
EXIT_INPUT_ERROR = 1


def positive_int(text: str) -> int:
    """Convierte un argumento a entero positivo o informa el error a ``argparse``."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"se esperaba un entero positivo, no {text!r}") from None
    if value < 1:
        raise argparse.ArgumentTypeError(f"se esperaba un entero positivo, no {value}")
    return value


def build_parser() -> argparse.ArgumentParser:
    """Argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description=(
            "Simula una máquina de Turing de una cinta descrita en YAML sobre cada cadena de "
            "simulation_strings y muestra todas las descripciones instantáneas."
        ),
    )
    parser.add_argument("--machine", required=True, metavar="ARCHIVO", help="archivo YAML de la máquina")
    parser.add_argument(
        "--max-steps",
        type=positive_int,
        default=DEFAULT_MAX_STEPS,
        metavar="N",
        help=f"máximo de transiciones por cadena (por defecto {DEFAULT_MAX_STEPS})",
    )
    return parser


def describe_machine(machine: TuringMachine, blank: str) -> list[str]:
    """Resumen formal M = (Q, Σ, Γ, δ, q0, B, F) con la tabla δ completa, en el orden del YAML."""

    def symbols(values: frozenset) -> str:
        ordered = sorted(values, key=lambda s: (s is BLANK, s or ""))
        return "{" + ", ".join(show_symbol(s, blank) for s in ordered) + "}"

    width = len(str(len(machine.transitions)))
    return [
        f"Q  = {{{', '.join(sorted(machine.states))}}}",
        f"Σ  = {symbols(machine.input_alphabet)}",
        f"Γ  = {symbols(machine.tape_alphabet)}",
        f"q0 = {machine.initial_state}",
        f"F  = {{{', '.join(sorted(machine.final_states))}}}",
        f"B  = {blank} (blanco)",
        f"δ  = {len(machine.transitions)} reglas" + (", en el orden del YAML:" if machine.transitions else ""),
        *(f"  {number:>{width}}. {format_rule(rule, blank)}" for number, rule in enumerate(machine.transitions, start=1)),
    ]


def run(path: str, max_steps: int, out: TextIO, err: TextIO) -> int:
    """Carga ``path``, simula sus cadenas y escribe los reportes; devuelve el código de salida."""
    try:
        machine, strings = parse_machine(load_yaml(path))
        validate_machine(machine, strings)
    except InputError as error:
        print(f"error: {error}", file=err)
        return EXIT_INPUT_ERROR

    blank = blank_glyph(machine)
    print(f"Máquina: {path}", file=out)
    for line in describe_machine(machine, blank):
        print(f"  {line}", file=out)
    print(f"Cadenas: {len(strings)} · límite de pasos por cadena: {max_steps}", file=out)
    if not strings:
        print("El archivo no contiene cadenas en simulation_strings.", file=out)
        return EXIT_OK

    traces = []
    for number, word in enumerate(strings, start=1):
        trace = build_trace(simulate(machine, word, max_steps))
        traces.append(trace)
        print(file=out)
        for line in format_result(trace, number, len(strings), blank):
            print(line, file=out)

    print(file=out)
    print("=== Resumen ===", file=out)
    for line in format_summary(traces, blank):
        print(line, file=out)
    return EXIT_OK


def _use_utf8(*streams: TextIO) -> None:
    """Escribe en UTF-8 aunque la consola o la redirección usen otra codificación (δ, ⊢, ε)."""
    for stream in streams:
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada; ``argv`` sin el nombre del programa (``None`` usa ``sys.argv``)."""
    _use_utf8(sys.stdout, sys.stderr)
    args = build_parser().parse_args(argv)
    return run(args.machine, args.max_steps, sys.stdout, sys.stderr)


if __name__ == "__main__":
    sys.exit(main())

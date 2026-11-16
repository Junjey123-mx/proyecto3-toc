"""Simulador de máquinas de Turing de una cinta definidas en YAML.

Uso:
    python main.py --machine machines/<archivo>.yaml [--max-steps N]
    python main.py --interactive [--max-steps N]

Con ``--machine`` lee la máquina y su lista ``simulation_strings``, simula cada
cadena en orden y escribe en la salida estándar la descripción formal de la
máquina (con la tabla δ completa), el reporte de cada cadena (veredicto, cinta
final y todas las IDs) y un resumen. Los errores del archivo se escriben en la
salida de errores.

Con ``--interactive`` abre un menú numérico con las cuatro máquinas del
proyecto (``src/cli/interactive_menu.py``): muestra la ficha técnica de la
máquina elegida y ejecuta una cadena por vez, predefinida o ingresada en la
terminal, con el mismo reporte completo.

Códigos de salida: 0 si todas las cadenas se simularon (aceptadas, rechazadas o
detenidas por el límite de pasos) o si el menú se cerró normalmente, 1 si el
archivo no se pudo cargar o la máquina no es válida, 2 si los argumentos son
incorrectos y 130 si el menú se interrumpió con Ctrl+C.
"""

import argparse
import sys
from collections.abc import Sequence
from typing import TextIO

from src.cli.interactive_menu import run_menu
from src.input.errors import InputError
from src.input.machine_parser import parse_machine
from src.input.machine_validator import validate_machine
from src.input.yaml_loader import load_yaml
from src.output.machine_formatter import describe_machine
from src.output.result_formatter import format_result, format_summary
from src.simulator.engine import DEFAULT_MAX_STEPS, simulate
from src.simulator.trace import build_trace
from src.utils.notation import blank_glyph

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
            "simulation_strings y muestra todas las descripciones instantáneas. Con --interactive "
            "abre un menú con las cuatro máquinas del proyecto."
        ),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--machine", metavar="ARCHIVO", help="archivo YAML de la máquina")
    mode.add_argument(
        "--interactive",
        action="store_true",
        help="menú numérico con las cuatro máquinas del proyecto; ejecuta una cadena por vez",
    )
    parser.add_argument(
        "--max-steps",
        type=positive_int,
        default=DEFAULT_MAX_STEPS,
        metavar="N",
        help=f"máximo de transiciones por cadena (por defecto {DEFAULT_MAX_STEPS})",
    )
    return parser


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
    if args.interactive:
        return run_menu(max_steps=args.max_steps)
    return run(args.machine, args.max_steps, sys.stdout, sys.stderr)


if __name__ == "__main__":
    sys.exit(main())

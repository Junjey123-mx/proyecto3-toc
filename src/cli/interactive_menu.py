"""Menú interactivo: elegir una máquina del catálogo, ver su ficha técnica y ejecutar una cadena por vez.

El menú solo navega y presenta. Cada máquina se carga con ``load_yaml`` →
``parse_machine`` → ``validate_machine``, cada cadena se ejecuta con
``simulate`` → ``build_trace`` y ``simulation_view`` ordena el resultado en
bloques (inicio, procedimiento, configuración final, veredicto, fin) con las
mismas líneas de IDs y de configuración que imprime ``python main.py
--machine``: la traza de una cadena es la misma en los dos modos. La ficha
técnica se muestra al elegir la máquina, no después de cada ejecución. Las
cadenas ingresadas se guardan en memoria durante la sesión y nunca se escriben
en el YAML.

Dos contextos de entrada separados: en un menú solo se aceptan los números de
sus opciones; al ingresar una cadena, el texto se valida contra Σ y contra el
formato de la máquina, y si no es válido se ofrece reintentar o regresar.
"""

import sys
import textwrap
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TextIO

from src.cli.machine_catalog import CATALOG, CatalogEntry
from src.cli.simulation_view import format_simulation
from src.input.errors import InputError
from src.input.machine_parser import parse_machine
from src.input.machine_validator import validate_machine
from src.input.yaml_loader import load_yaml
from src.model.turing_machine import TuringMachine
from src.output.machine_formatter import cache_values, format_delta_table, format_symbols, formal_components
from src.output.result_formatter import show_word
from src.simulator.engine import DEFAULT_MAX_STEPS, simulate
from src.simulator.trace import build_trace
from src.utils.notation import blank_glyph

RULE = "=" * 41
WIDTH = 96
PREDEFINED = "predefinida"
ADDED = "agregada en sesión"
EXIT_INTERRUPTED = 130
PAUSE = "Presione ENTER para regresar al submenú..."


@dataclass
class Session:
    """Una máquina abierta: su definición cargada y la lista de cadenas de esta sesión."""

    entry: CatalogEntry
    machine: TuringMachine
    blank: str
    strings: list[tuple[str, str]] = field(default_factory=list)
    """Pares (cadena, origen): primero las del YAML, luego las agregadas, sin repetir."""


class Menu:
    """Navegación numérica; ``read`` funciona como ``input`` (lanza ``EOFError`` al terminar la entrada)."""

    def __init__(self, read: Callable[[str], str], out: TextIO, max_steps: int = DEFAULT_MAX_STEPS) -> None:
        self.read, self.out, self.max_steps = read, out, max_steps
        self.sessions: dict[str, Session] = {}

    def run(self) -> int:
        """Muestra el menú principal hasta «Salir», el fin de la entrada o Ctrl+C."""
        try:
            self.main_menu()
        except EOFError:
            self.say("", "Fin de la entrada: el simulador se cierra.")
        except KeyboardInterrupt:
            self.say("", "Interrumpido con Ctrl+C: el simulador se cierra.")
            return EXIT_INTERRUPTED
        return 0

    # Navegación

    def main_menu(self) -> None:
        while True:
            self.banner("SIMULADOR DE MÁQUINAS DE TURING")
            labels = [entry.menu_label for entry in CATALOG]
            choice = self.choose([*labels, "Salir"], "Seleccione una opción: ")
            if choice > len(CATALOG):
                self.say("", "Hasta luego.")
                return
            session = self.open(CATALOG[choice - 1])
            if session is not None:
                self.machine_menu(session)

    def machine_menu(self, session: Session) -> None:
        options = ["Cadenas disponibles", "Ingresar una cadena nueva", "Regresar al menú principal"]
        while True:
            self.banner("MÁQUINA SELECCIONADA")
            self.say("", session.entry.menu_label)
            choice = self.choose(options, "Seleccione una opción: ")
            if choice == 1:
                self.strings_menu(session)
            elif choice == 2:
                self.new_string(session)
            else:
                return

    def strings_menu(self, session: Session) -> None:
        while True:
            self.say("", f"CADENAS DISPONIBLES — {session.entry.title}")
            width = max(len(show_word(word)) for word, _ in session.strings) if session.strings else 0
            items = [f"{show_word(word):<{width}}  [{origin}]" for word, origin in session.strings]
            choice = self.choose([*items, "Regresar"], "Seleccione una cadena: ")
            if choice > len(session.strings):
                return
            self.execute(session, session.strings[choice - 1][0])

    def new_string(self, session: Session) -> None:
        entry, machine = session.entry, session.machine
        self.say(
            "",
            "INGRESAR NUEVA CADENA",
            "",
            f"Máquina: {entry.title}",
            f"Alfabeto permitido: {format_symbols(machine.input_alphabet)}",
            f"Formato: {entry.domain_text}",
        )
        if entry.admits(""):
            self.say("Deje la línea vacía para ingresar la cadena vacía (ε).")
        while True:
            word = self.read("Ingrese una cadena: ").strip()
            problem = self.problem(session, word)
            if problem is None:
                break
            self.say(f"Cadena no válida: {problem}")
            if self.choose(["Intentar de nuevo", "Regresar al submenú"], "Seleccione una opción: ") == 2:
                return
        known = [existing for existing, _ in session.strings]
        if word in known:
            self.say(f"{show_word(word)} ya está en la lista (n.º {known.index(word) + 1}); no se duplica.")
        else:
            session.strings.append((word, ADDED))
            self.say(f"{show_word(word)} se agregó a la lista de esta sesión (n.º {len(session.strings)}).")
        self.execute(session, word)

    # Máquinas y cadenas

    def open(self, entry: CatalogEntry) -> Session | None:
        """Carga la máquina la primera vez (la sesión se conserva) y muestra su ficha sin simular nada."""
        session = self.sessions.get(entry.file)
        if session is None:
            try:
                machine, strings = parse_machine(load_yaml(entry.path))
                validate_machine(machine, strings)
            except InputError as error:
                self.say("", f"No se pudo cargar {entry.file}:", str(error))
                return None
            session = Session(entry, machine, blank_glyph(machine))
            for word in strings:
                if word not in [existing for existing, _ in session.strings]:
                    session.strings.append((word, PREDEFINED))
            self.sessions[entry.file] = session
        self.show_sheet(session)
        return session

    def problem(self, session: Session, word: str) -> str | None:
        """Motivo por el que ``word`` no se puede ejecutar, o ``None`` si es válida."""
        outside = sorted(set(word) - session.machine.input_alphabet)
        if outside:
            symbols = ", ".join(repr(symbol) for symbol in outside)
            alphabet = format_symbols(session.machine.input_alphabet)
            return f"{show_word(word)} usa símbolos fuera del alfabeto {alphabet}: {symbols}."
        if not session.entry.admits(word):
            return f"{show_word(word)} no tiene el formato esperado: {session.entry.domain_text}."
        return None

    def execute(self, session: Session, word: str) -> None:
        """Simula solo ``word`` con el motor, muestra la ejecución completa y espera ENTER para volver."""
        trace = build_trace(simulate(session.machine, word, self.max_steps))
        label = f"{session.entry.menu_label} ({session.entry.file})"
        self.say("", *format_simulation(trace, label, session.entry.recognizer, session.blank), "")
        self.read(PAUSE)

    def show_sheet(self, session: Session) -> None:
        """Ficha técnica: componentes y δ leídos del YAML, más la explicación del catálogo."""
        entry, machine, blank = session.entry, session.machine, session.blank
        self.banner(entry.menu_label)
        self.paragraph("A. Máquina: ", f"{entry.title} — machines/{entry.file}")
        self.paragraph("B. Objetivo formal: ", entry.objective)
        self.paragraph("C. Lenguaje reconocido: " if entry.recognizer else "C. Transformación: ", entry.function)
        self.say("", "D. Componentes formales (leídos del YAML):")
        self.say(*(f"   {line}" for line in formal_components(machine, blank)))
        self.say(f"   Caché: valores que aparecen en δ = {format_symbols(cache_values(machine), blank)}")
        self.say(f"   Reglas de δ: {len(machine.transitions)}")
        self.say("", "E. Tabla δ completa, en el orden del YAML:")
        self.say(*(f"   {line}" for line in format_delta_table(machine, blank)))
        self.say("", "F. Procedimiento mecanizado")
        self.say("   Fases:")
        for number, phase in enumerate(entry.phases, start=1):
            self.paragraph(f"     {number}. ", phase)
        self.say("   Estados:")
        for state in sorted(entry.states):
            self.paragraph(f"     {state:<4}", entry.states[state])
        self.say("   Marcadores y separadores de la cinta:")
        for symbol, meaning in entry.symbols.items():
            self.paragraph(f"     {symbol:<4}", meaning)
        if not entry.symbols:
            self.say("     Ninguno: Γ = Σ ∪ {B}.")
        self.paragraph("   Caché: ", entry.cache)
        self.paragraph("   Terminación: ", entry.halting)
        label = "G. Aceptación y rechazo: " if entry.recognizer else "G. Transformación completa: "
        self.paragraph(label, entry.outcome)

    # Entrada y salida

    def choose(self, options: Sequence[str], prompt: str) -> int:
        """Muestra las opciones numeradas y devuelve la elegida (1 … n); reintenta ante cualquier otra entrada."""
        self.say("", *(f"{number}. {text}" for number, text in enumerate(options, start=1)), "")
        valid = {str(number) for number in range(1, len(options) + 1)}
        while True:
            text = self.read(prompt).strip()
            if text in valid:
                return int(text)
            if text:
                self.say(f"Opción no válida: {text!r}. Escriba un número del 1 al {len(options)}.")
            else:
                self.say(f"No escribió ninguna opción. Escriba un número del 1 al {len(options)}.")

    def banner(self, title: str) -> None:
        self.say("", RULE, title.center(len(RULE)).rstrip(), RULE)

    def paragraph(self, lead: str, text: str) -> None:
        indent = " " * (len(lead) - len(lead.lstrip()) + 3)
        self.say(textwrap.fill(text, WIDTH, initial_indent=lead, subsequent_indent=indent))

    def say(self, *lines: str) -> None:
        for line in lines:
            print(line, file=self.out)


def run_menu(read: Callable[[str], str] = input, out: TextIO | None = None, max_steps: int = DEFAULT_MAX_STEPS) -> int:
    """Ejecuta el menú interactivo; devuelve 0 al salir o al terminar la entrada y 130 con Ctrl+C."""
    return Menu(read, out if out is not None else sys.stdout, max_steps).run()

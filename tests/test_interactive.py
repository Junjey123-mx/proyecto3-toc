"""Menú interactivo: navegación, ficha técnica, ejecución individual, validación y equivalencia con --machine.

La entrada del usuario se simula con ``Keyboard``, que entrega líneas en orden
y lanza ``EOFError`` cuando se agotan (como ``input``). Cada ejecución termina en
una pausa, que se contesta con ``ENTER`` (una línea vacía). Las secciones de
cada ejecución del menú se comparan con la salida real de ``main.run`` para las
mismas cadenas.
"""

import io
import re
import signal
import subprocess
import sys
from pathlib import Path

import pytest

import main
import src.cli.interactive_menu as interactive
from src.cli import machine_catalog
from src.cli.interactive_menu import ADDED, EXIT_INTERRUPTED, PAUSE, PREDEFINED, RULE, run_menu
from src.cli.machine_catalog import CATALOG
from src.cli.simulation_view import LIMIT_NOTE, MAJOR, MINOR, format_verdict
from src.input.machine_parser import parse_machine
from src.input.yaml_loader import load_yaml
from src.model.transition import BLANK
from src.output.id_formatter import format_id
from src.output.machine_formatter import format_delta_table, formal_components
from src.output.result_formatter import BLANK_TAPE
from src.output.tape_formatter import tape_contents
from src.simulator.engine import simulate
from src.simulator.trace import build_trace
from src.utils.notation import blank_glyph, format_rule, show_symbol

ROOT = Path(__file__).resolve().parents[1]
RECOGNIZER, INCREMENT, REVERSE, ADDITION = "1", "2", "3", "4"
EXIT = "5"
STRINGS, NEW, BACK = "1", "2", "3"
"""Opciones del submenú de una máquina."""
ENTER = ""
"""Respuesta a la pausa que sigue a cada ejecución."""
SECTIONS = ("PROCEDIMIENTO PASO A PASO", "CONFIGURACIÓN FINAL", "VEREDICTO FINAL")
"""Secciones de una ejecución entre «INICIO DE SIMULACIÓN» y «FIN DE SIMULACIÓN», en orden."""


class Keyboard:
    """Entrada simulada: devuelve las líneas en orden, ``EOFError`` al agotarse; registra los prompts."""

    def __init__(self, *lines):
        self.lines = list(lines)
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        if not self.lines:
            raise EOFError
        line = self.lines.pop(0)
        if line is KeyboardInterrupt:
            raise KeyboardInterrupt
        return line


def menu(*lines, max_steps=10_000):
    out = io.StringIO()
    keyboard = Keyboard(*lines)
    code = run_menu(keyboard, out, max_steps)
    return code, out.getvalue(), keyboard


def loaded(entry):
    return parse_machine(load_yaml(entry.path))


def back_from_list(option, added=0):
    """Número de «Regresar» en la lista de cadenas: depende de cuántas cadenas tenga el YAML."""
    return str(len(loaded(CATALOG[int(option) - 1])[1]) + added + 1)


def listing(out, title):
    """Opciones (texto, origen) de la última lista de cadenas mostrada, hasta «Regresar» incluido."""
    lines = out.split(f"CADENAS DISPONIBLES — {title}")[-1].splitlines()
    items = []
    for line in lines:
        match = re.fullmatch(r"\d+\. (.+?)(?:\s+\[(.+)\])?", line)
        if match:
            items.append((match.group(1), match.group(2) or ""))
            if match.group(1) == "Regresar":
                return items
    raise AssertionError("no se encontró la lista de cadenas")


def trim(lines):
    """Quita las líneas vacías y los separadores de los extremos de una sección."""
    while lines and not lines[0].strip("=- "):
        lines = lines[1:]
    while lines and not lines[-1].strip("=- "):
        lines = lines[:-1]
    return lines


def simulations(out):
    """Ejecuciones del menú en orden: (cadena, {sección: líneas}) por cada bloque INICIO … FIN."""
    runs = []
    for block in out.split("INICIO DE SIMULACIÓN\n")[1:]:
        assert "FIN DE SIMULACIÓN" in block, "ejecución sin cierre"
        body = block.split("FIN DE SIMULACIÓN")[0]
        parts = re.split(rf"^ *({'|'.join(SECTIONS)})$", body, flags=re.MULTILINE)
        assert parts[1::2] == list(SECTIONS), "secciones fuera de orden"
        sections = {"INICIO DE SIMULACIÓN": trim(parts[0].splitlines())}
        sections |= {title: trim(text.splitlines()) for title, text in zip(parts[1::2], parts[2::2])}
        entered = re.fullmatch(r"Cadena de entrada: (?:'(.*)'|ε \(cadena vacía\))", sections["INICIO DE SIMULACIÓN"][1])
        runs.append((entered.group(1) or "", sections))
    return runs


def menu_reports(out):
    """Ejecuciones del menú agrupadas por cadena: {cadena: [secciones, …]}."""
    reports = {}
    for word, sections in simulations(out):
        reports.setdefault(word, []).append(sections)
    return reports


def cli_reports(path):
    """Reportes de ``python main.py --machine``: {cadena: líneas del reporte sin el encabezado}."""
    out, err = io.StringIO(), io.StringIO()
    assert main.run(str(path), 10_000, out, err) == main.EXIT_OK
    reports = {}
    for block in out.getvalue().split("\n\n=== Resumen ===")[0].split("\n\n=== Cadena ")[1:]:
        lines = block.splitlines()
        word = re.fullmatch(r"\d+ de \d+: (?:'(.*)'|ε \(cadena vacía\)) \(longitud \d+\) ===", lines[0]).group(1) or ""
        reports[word] = lines[1:]
    return reports


# Menú principal y navegación


def test_main_menu_lists_the_four_machines_and_exit_without_a_yaml_option():
    code, out, keyboard = menu(EXIT)
    assert code == 0
    assert "SIMULADOR DE MÁQUINAS DE TURING" in out
    assert [line for line in out.splitlines() if re.fullmatch(r"\d\. .+", line)] == [
        "1. Reconocedora — a^n b^n",
        "2. Alteradora — Incremento binario",
        "3. Alteradora — Inversión de cadenas",
        "4. Alteradora — Suma binaria",
        "5. Salir",
    ]
    assert "yaml" not in out.lower() and "cargar" not in out.lower()
    assert out.rstrip().endswith("Hasta luego.")
    assert keyboard.prompts == ["Seleccione una opción: "]


@pytest.mark.parametrize("wrong", ["", "   ", "0", "6", "abc", "1.0", "-1", "10101", "１"])
def test_invalid_options_are_retried_without_leaving_the_menu(wrong):
    code, out, keyboard = menu(wrong, EXIT)
    assert code == 0
    assert ("No escribió ninguna opción" if not wrong.strip() else f"Opción no válida: {wrong.strip()!r}") in out
    assert "INICIO DE SIMULACIÓN" not in out and "MÁQUINA SELECCIONADA" not in out
    assert len(keyboard.prompts) == 2


def test_option_with_surrounding_spaces_is_accepted():
    _, out, _ = menu(f"  {INCREMENT} ", BACK, EXIT)
    assert "A. Máquina: Incremento binario — machines/transformer_binary_increment.yaml" in out
    assert "MÁQUINA SELECCIONADA\n=========================================\n\nAlteradora — Incremento binario\n" in out


@pytest.mark.parametrize(("option", "entry"), list(zip("1234", CATALOG)))
def test_selecting_a_machine_shows_its_sheet_without_running_any_string(option, entry):
    machine, _ = loaded(entry)
    blank = blank_glyph(machine)
    _, out, _ = menu(option, BACK, EXIT)
    lines = out.splitlines()
    assert "INICIO DE SIMULACIÓN" not in out
    assert f"A. Máquina: {entry.title} — machines/{entry.file}" in lines
    for line in formal_components(machine, blank):
        assert f"   {line}" in lines
    assert f"   Reglas de δ: {len(machine.transitions)}" in lines
    table = format_delta_table(machine, blank)
    start = lines.index(f"   {table[0]}")
    assert lines[start:start + len(table)] == [f"   {row}" for row in table]
    assert len(table) == len(machine.transitions) + 1
    assert "F. Procedimiento mecanizado" in lines and ("   Caché: " + entry.cache[:30]) in out
    for number, phase in enumerate(entry.phases, start=1):
        assert f"     {number}. {phase.split()[0]}" in out
    assert lines.count("           MÁQUINA SELECCIONADA") == 1


def test_delta_table_columns_follow_the_yaml_rule_by_rule():
    machine, _ = loaded(CATALOG[1])
    assert format_delta_table(machine) == [
        "#  Estado  Caché  Lee  Estado sig.  Caché sig.  Escribe  Mov",
        "1  q0      B      0    q0           B           0        R",
        "2  q0      B      1    q0           B           1        R",
        "3  q0      B      B    q1           1           B        L",
        "4  q1      1      1    q1           1           0        L",
        "5  q1      1      0    q2           B           1        S",
        "6  q1      1      B    q2           B           1        S",
    ]


def test_submenu_has_three_options_and_no_separate_information_option():
    _, out, keyboard = menu(REVERSE, "4", BACK, EXIT)
    submenu = out.split("MÁQUINA SELECCIONADA")[1].split("SIMULADOR DE MÁQUINAS DE TURING")[0]
    assert [line for line in submenu.splitlines() if re.fullmatch(r"\d\. .+", line)] == [
        "1. Cadenas disponibles",
        "2. Ingresar una cadena nueva",
        "3. Regresar al menú principal",
    ]
    assert "Opción no válida: '4'. Escriba un número del 1 al 3." in out
    assert "Ver información" not in out
    assert out.count("A. Máquina: Inversión de cadenas") == 1
    assert "INICIO DE SIMULACIÓN" not in out
    assert len(keyboard.prompts) == 4


def test_back_options_return_to_the_submenu_and_to_the_main_menu():
    _, out, keyboard = menu(RECOGNIZER, STRINGS, back_from_list(RECOGNIZER), BACK, EXIT)
    assert keyboard.prompts == [
        "Seleccione una opción: ",
        "Seleccione una opción: ",
        "Seleccione una cadena: ",
        "Seleccione una opción: ",
        "Seleccione una opción: ",
    ]
    assert out.count("MÁQUINA SELECCIONADA") == 2
    assert out.count("SIMULADOR DE MÁQUINAS DE TURING") == 2
    assert out.rstrip().endswith("Hasta luego.")


# Cadenas disponibles y ejecución individual


@pytest.mark.parametrize(("option", "entry"), list(zip("1234", CATALOG)))
def test_available_strings_are_the_yaml_strings_in_order(option, entry):
    _, strings = loaded(entry)
    _, out, _ = menu(option, STRINGS, back_from_list(option), BACK, EXIT)
    items = listing(out, entry.title)
    assert [text for text, _ in items[:-1]] == [f"'{word}'" if word else "ε (cadena vacía)" for word in strings]
    assert {origin for _, origin in items[:-1]} == {PREDEFINED}
    assert items[-1] == ("Regresar", "")


@pytest.mark.parametrize(("option", "entry"), list(zip("1234", CATALOG)))
def test_each_predefined_string_runs_alone_and_matches_the_machine_mode(option, entry):
    _, strings = loaded(entry)
    expected = cli_reports(entry.path)
    for number, word in enumerate(strings, start=1):
        _, out, _ = menu(option, STRINGS, str(number), ENTER, back_from_list(option), BACK, EXIT)
        reports = menu_reports(out)
        assert list(reports) == [word]
        [sections] = reports[word]
        cli = expected[word]
        result, reason, steps = (line.split(maxsplit=1)[1] for line in cli[:3])
        procedure = cli.index(f"Descripciones instantáneas (ID_0 a ID_{steps}):")
        assert sections["INICIO DE SIMULACIÓN"] == [
            f"Máquina: {entry.menu_label} ({entry.file})",
            f"Cadena de entrada: '{word}'" if word else "Cadena de entrada: ε (cadena vacía)",
            f"Longitud: {len(word)}",
        ]
        assert sections["PROCEDIMIENTO PASO A PASO"] == cli[procedure:]
        assert sections["CONFIGURACIÓN FINAL"] == cli[3:procedure - 1]
        verdict = sections["VEREDICTO FINAL"]
        assert verdict[0].strip().startswith(f"{result.split()[0]} — ")
        assert f"Pasos realizados: {steps}" in verdict
        assert verdict[verdict.index("Motivo:") + 1] == f"{reason[0].upper()}{reason[1:]}."


def test_report_shows_every_id_and_the_rule_applied_at_each_step():
    _, out, _ = menu(INCREMENT, STRINGS, "3", ENTER, back_from_list(INCREMENT), BACK, EXIT)
    report = menu_reports(out)["11111"][0]
    procedure = report["PROCEDIMIENTO PASO A PASO"]
    assert procedure[0] == "Descripciones instantáneas (ID_0 a ID_12):"
    rows = procedure[2:]
    assert [int(row.split()[0]) for row in rows] == list(range(13))
    assert rows[0].split()[1:] == ["[q0,B]11111", "—"]
    assert rows[-1] == "    12  [q2,B]100000  δ([q1, 1], B) = ([q2, B], 1, S)"
    final = report["CONFIGURACIÓN FINAL"]
    assert "Cinta final:   100000" in final and "cabezal   ^" in final


def test_menu_strings_are_simulated_by_the_generic_engine(monkeypatch):
    calls = []
    real = interactive.simulate

    def spy(machine, word, max_steps):
        calls.append((machine.initial_state, len(machine.transitions), word, max_steps))
        return real(machine, word, max_steps)

    monkeypatch.setattr(interactive, "simulate", spy)
    menu(ADDITION, NEW, "1001#11", ENTER, STRINGS, "1", ENTER, back_from_list(ADDITION, 1), BACK, EXIT, max_steps=500)
    assert calls == [("q0", 57, "1001#11", 500), ("q0", 57, "1011#0110", 500)]


def test_max_steps_reaches_the_engine_and_limit_is_not_a_rejection():
    _, out, _ = menu(RECOGNIZER, STRINGS, "2", ENTER, back_from_list(RECOGNIZER), BACK, EXIT, max_steps=30)
    verdict = menu_reports(out)["aaaabbbb"][0]["VEREDICTO FINAL"]
    assert verdict[0].strip() == "LIMIT_EXCEEDED — LÍMITE DE PASOS ALCANZADO"
    assert "Pasos realizados: 30" in verdict and "REJECTED" not in "".join(verdict)


# Cadenas nuevas


def test_new_string_is_validated_added_and_run_immediately():
    _, out, _ = menu(INCREMENT, NEW, "0111", ENTER, BACK, EXIT)
    assert "Alfabeto permitido: {0, 1}" in out
    assert "'0111' se agregó a la lista de esta sesión" in out
    report = menu_reports(out)["0111"][0]
    assert "Cinta final:   1000" in report["CONFIGURACIÓN FINAL"]


def test_new_strings_keep_leading_zeros():
    _, out, _ = menu(REVERSE, NEW, "00110", ENTER, BACK, EXIT)
    assert "Cinta final:   01100" in menu_reports(out)["00110"][0]["CONFIGURACIÓN FINAL"]


@pytest.mark.parametrize(
    ("option", "word", "message"),
    [
        (INCREMENT, "1021", "'1021' usa símbolos fuera del alfabeto {0, 1}: '2'."),
        (INCREMENT, "10 01", "'10 01' usa símbolos fuera del alfabeto {0, 1}: ' '."),
        (INCREMENT, "", "ε (cadena vacía) no tiene el formato esperado"),
        (RECOGNIZER, "abc", "'abc' usa símbolos fuera del alfabeto {a, b}: 'c'."),
        (REVERSE, "10o1", "'10o1' usa símbolos fuera del alfabeto {0, 1}: 'o'."),
        (ADDITION, "1011", "'1011' no tiene el formato esperado: A#B"),
        (ADDITION, "1#0#1", "'1#0#1' no tiene el formato esperado"),
        (ADDITION, "#01", "'#01' no tiene el formato esperado"),
        (ADDITION, "01#", "'01#' no tiene el formato esperado"),
        (ADDITION, "", "ε (cadena vacía) no tiene el formato esperado"),
        (ADDITION, "1a#0", "'1a#0' usa símbolos fuera del alfabeto {#, 0, 1}: 'a'."),
    ],
)
def test_invalid_strings_are_diagnosed_and_never_simulated(option, word, message):
    _, out, keyboard = menu(option, NEW, word, "2", BACK, EXIT)
    assert f"Cadena no válida: {message}" in out
    assert "INICIO DE SIMULACIÓN" not in out
    assert keyboard.prompts.count("Ingrese una cadena: ") == 1


def test_retry_after_an_invalid_string():
    _, out, keyboard = menu(ADDITION, NEW, "10#", "1", "10#1", ENTER, BACK, EXIT)
    assert keyboard.prompts.count("Ingrese una cadena: ") == 2
    assert list(menu_reports(out)) == ["10#1"]
    assert "Cinta final:   11" in menu_reports(out)["10#1"][0]["CONFIGURACIÓN FINAL"]


@pytest.mark.parametrize(("option", "admitted"), [(RECOGNIZER, True), (REVERSE, True), (INCREMENT, False)])
def test_empty_line_is_the_empty_string_only_where_the_domain_admits_it(option, admitted):
    code, out, _ = menu(option, NEW, "")
    assert code == 0
    assert ("Deje la línea vacía para ingresar la cadena vacía (ε)." in out) is admitted
    assert ("ε (cadena vacía) se agregó" in out) is admitted
    assert list(menu_reports(out)) == ([""] if admitted else [])


def test_a_digit_typed_as_an_option_is_never_taken_as_a_string():
    _, out, _ = menu("1", "1", "1", ENTER, back_from_list(RECOGNIZER), BACK, EXIT)
    assert list(menu_reports(out)) == ["aaabbb"]
    assert "se agregó" not in out


def test_session_strings_persist_when_returning_to_the_main_menu():
    _, out, _ = menu(REVERSE, NEW, "0011", ENTER, BACK, REVERSE, STRINGS, back_from_list(REVERSE, 1), BACK, EXIT)
    assert listing(out, "Inversión de cadenas")[-2:] == [("'0011'", ADDED), ("Regresar", "")]


def test_repeated_strings_are_not_duplicated_in_the_list():
    added = back_from_list(INCREMENT)
    _, out, _ = menu(INCREMENT, NEW, "10101", ENTER, NEW, "0011", ENTER, NEW, "0011", ENTER, STRINGS,
                     back_from_list(INCREMENT, 1), BACK, EXIT)
    assert "'10101' ya está en la lista (n.º 1); no se duplica." in out
    assert f"'0011' ya está en la lista (n.º {added}); no se duplica." in out
    assert [text for text, _ in listing(out, "Incremento binario")].count("'0011'") == 1
    assert len(menu_reports(out)["0011"]) == 2


def test_session_strings_do_not_leak_between_machines():
    _, out, _ = menu(INCREMENT, NEW, "0110", ENTER, BACK, REVERSE, STRINGS, back_from_list(REVERSE), BACK, EXIT)
    assert ("'0110'", ADDED) not in listing(out, "Inversión de cadenas")


def test_session_never_writes_the_yaml_files():
    before = {entry.file: entry.path.read_bytes() for entry in CATALOG}
    menu(INCREMENT, NEW, "0110", ENTER, BACK, ADDITION, NEW, "1#1", ENTER, BACK, EXIT)
    assert {entry.file: entry.path.read_bytes() for entry in CATALOG} == before


# Presentación de cada ejecución: inicio, procedimiento, configuración final, veredicto, fin


def test_sheet_is_shown_once_per_selection_and_not_after_each_run():
    sheet = "A. Máquina: Reconocedora aⁿbⁿ — machines/recognizer_anbn.yaml"
    _, out, _ = menu(RECOGNIZER, STRINGS, "1", ENTER, "3", ENTER, back_from_list(RECOGNIZER), NEW, "ab", ENTER,
                     BACK, RECOGNIZER, BACK, EXIT)
    assert out.count(sheet) == 2
    assert out.index(sheet) < out.index("INICIO DE SIMULACIÓN")
    assert out.count("FIN DE SIMULACIÓN") == 3
    assert out.rindex("FIN DE SIMULACIÓN") < out.rindex(sheet)
    assert [word for word, _ in simulations(out)] == ["aaabbb", "aaabb", "ab"]


@pytest.mark.parametrize(("option", "entry"), list(zip("1234", CATALOG)))
def test_every_run_has_the_same_delimited_layout_and_complete_data(option, entry):
    machine, strings = loaded(entry)
    blank, word = blank_glyph(machine), strings[0]
    trace = build_trace(simulate(machine, word))
    _, out, _ = menu(option, STRINGS, "1", ENTER, back_from_list(option), BACK, EXIT)
    lines = out.splitlines()
    titles = ["INICIO DE SIMULACIÓN", "PROCEDIMIENTO PASO A PASO", "CONFIGURACIÓN FINAL", "VEREDICTO FINAL",
              "FIN DE SIMULACIÓN"]
    found = [index for index, line in enumerate(lines) if line.strip() in titles]
    assert [lines[index].strip() for index in found] == titles
    for index, rule in zip(found, [MAJOR, MINOR, MINOR, MAJOR, MAJOR]):
        assert lines[index - 1] == lines[index + 1] == rule
        assert lines[index] == lines[index].strip().center(len(rule)).rstrip()

    [(_, sections)] = simulations(out)
    rows = [row.split(maxsplit=2) for row in sections["PROCEDIMIENTO PASO A PASO"][2:]]
    assert len(rows) == trace.steps + 1 == len(trace.entries)
    assert [int(row[0]) for row in rows] == list(range(trace.steps + 1))
    assert [row[1] for row in rows] == [format_id(step, len(word), blank) for step in trace.entries]
    assert rows[0][2] == "—"
    assert [row[2] for row in rows[1:]] == [format_rule(step.applied, blank) for step in trace.entries[1:]]
    assert sections["CONFIGURACIÓN FINAL"][:5] == [
        f"Estado final:  {trace.final.state}",
        f"Caché final:   {show_symbol(trace.final.cache, blank)}",
        f"Cabezal final: {trace.final.head}",
        f"Cinta final:   {tape_contents(trace.final.tape, blank) or BLANK_TAPE}",
        f"ID final:      {rows[-1][1]}",
    ]


@pytest.mark.parametrize(
    ("option", "word", "max_steps", "verdict"),
    [
        (RECOGNIZER, "aaabbb", 10_000, ["ACCEPTED — CADENA ACEPTADA", "", "Cadena evaluada:  'aaabbb'",
                                        "Pasos realizados: 25", "", "Motivo:", "Alcanzó el estado final 'q4'."]),
        (RECOGNIZER, "aab", 10_000, ["REJECTED — CADENA RECHAZADA", "", "Cadena evaluada:  'aab'",
                                     "Pasos realizados: 7", "", "Motivo:",
                                     "No hay regla para el estado 'q1' con caché el blanco leyendo el blanco, "
                                     "y 'q1' no es final."]),
        (INCREMENT, "11111", 10_000, ["ACCEPTED — TRANSFORMACIÓN COMPLETADA", "", "Cadena original:  '11111'",
                                      "Cinta resultante: '100000'", "Pasos realizados: 12", "", "Motivo:",
                                      "Alcanzó el estado final 'q2'."]),
        (REVERSE, "10110", 10_000, ["ACCEPTED — TRANSFORMACIÓN COMPLETADA", "", "Cadena original:  '10110'",
                                    "Cinta resultante: '01101'", "Pasos realizados: 30", "", "Motivo:",
                                    "Alcanzó el estado final 'q6'."]),
        (REVERSE, "", 10_000, ["ACCEPTED — TRANSFORMACIÓN COMPLETADA", "", "Cadena original:  ε (cadena vacía)",
                               f"Cinta resultante: {BLANK_TAPE}", "Pasos realizados: 1", "", "Motivo:",
                               "Alcanzó el estado final 'q6'."]),
        (ADDITION, "10101#10111", 10_000, ["ACCEPTED — TRANSFORMACIÓN COMPLETADA", "",
                                           "Cadena original:  '10101#10111'", "Cinta resultante: '101100'",
                                           "Pasos realizados: 99", "", "Motivo:", "Alcanzó el estado final 'q9'."]),
        (RECOGNIZER, "aaabbb", 10, ["LIMIT_EXCEEDED — LÍMITE DE PASOS ALCANZADO", "", "Cadena evaluada:  'aaabbb'",
                                    "Pasos realizados: 10", "", "Motivo:",
                                    "Se aplicaron 10 transiciones y la máquina aún no se detiene.", *LIMIT_NOTE]),
        (ADDITION, "1#1", 5, ["LIMIT_EXCEEDED — LÍMITE DE PASOS ALCANZADO", "", "Cadena evaluada:  '1#1'",
                              "Pasos realizados: 5", "", "Motivo:",
                              "Se aplicaron 5 transiciones y la máquina aún no se detiene.", *LIMIT_NOTE]),
    ],
    ids=["aceptada", "rechazada", "incremento", "inversión", "inversión-ε", "suma", "límite", "límite-suma"],
)
def test_final_verdict_states_the_engine_outcome_and_its_reason(option, word, max_steps, verdict):
    _, out, _ = menu(option, NEW, word, ENTER, BACK, EXIT, max_steps=max_steps)
    [(entered, sections)] = simulations(out)
    body = sections["VEREDICTO FINAL"]
    assert entered == word
    assert [body[0].strip(), *body[1:]] == verdict


def test_a_rejection_in_a_transformer_is_not_presented_as_a_completed_transformation():
    """El menú no deja simular «1011» en la suma (falta #), pero la máquina sí lo rechaza: el titular lo dice."""
    machine, _ = loaded(CATALOG[3])
    trace = build_trace(simulate(machine, "1011"))
    verdict = format_verdict(trace, recognizer=False, blank=blank_glyph(machine))
    assert [verdict[4].strip(), *verdict[5:]] == [
        "REJECTED — PROCESAMIENTO RECHAZADO", "", "Cadena evaluada:  '1011'", f"Pasos realizados: {trace.steps}", "",
        "Motivo:", "No hay regla para el estado 'q1' con caché el blanco leyendo el blanco, y 'q1' no es final.",
    ]


def test_pause_waits_for_enter_before_the_menu_is_shown_again():
    out = io.StringIO()
    keyboard = Keyboard(RECOGNIZER, STRINGS, "1", ENTER, back_from_list(RECOGNIZER), BACK, EXIT)
    snapshots = []

    def read(prompt):
        snapshots.append((prompt, out.getvalue()))
        return keyboard(prompt)

    assert run_menu(read, out) == 0
    assert [prompt for prompt, _ in snapshots] == [
        "Seleccione una opción: ", "Seleccione una opción: ", "Seleccione una cadena: ", PAUSE,
        "Seleccione una cadena: ", "Seleccione una opción: ", "Seleccione una opción: ",
    ]
    at_pause, after_enter = snapshots[3][1], snapshots[4][1]
    assert at_pause.endswith(f"FIN DE SIMULACIÓN\n{MAJOR}\n\n")
    assert after_enter[len(at_pause):].lstrip("\n").startswith("CADENAS DISPONIBLES — Reconocedora aⁿbⁿ")


def test_end_of_input_at_the_pause_closes_the_menu_cleanly():
    code, out, keyboard = menu(RECOGNIZER, STRINGS, "1")
    assert code == 0 and keyboard.prompts[-1] == PAUSE
    assert out.index("FIN DE SIMULACIÓN") < out.index("Fin de la entrada: el simulador se cierra.")
    assert out.rstrip().endswith("Fin de la entrada: el simulador se cierra.")


def test_ctrl_c_at_the_pause_keeps_exit_code_130():
    code, out, keyboard = menu(ADDITION, STRINGS, "1", KeyboardInterrupt)
    assert code == EXIT_INTERRUPTED and keyboard.prompts[-1] == PAUSE
    assert out.rstrip().endswith("Interrumpido con Ctrl+C: el simulador se cierra.")


# Salida y robustez


def test_end_of_input_closes_the_menu_cleanly():
    code, out, _ = menu(ADDITION, NEW)
    assert code == 0
    assert out.rstrip().endswith("Fin de la entrada: el simulador se cierra.")


def test_ctrl_c_closes_the_menu_cleanly():
    code, out, _ = menu(REVERSE, STRINGS, KeyboardInterrupt)
    assert code == EXIT_INTERRUPTED == 130
    assert out.rstrip().endswith("Interrumpido con Ctrl+C: el simulador se cierra.")


def test_unloadable_machine_is_reported_and_the_menu_continues(monkeypatch, tmp_path):
    (tmp_path / CATALOG[0].file).write_text("q_states: [\n", encoding="utf-8")
    monkeypatch.setattr(machine_catalog, "MACHINES_DIR", tmp_path)
    code, out, _ = menu(RECOGNIZER, EXIT)
    assert code == 0
    assert f"No se pudo cargar {CATALOG[0].file}:" in out and "YAML inválido" in out
    assert out.count("SIMULADOR DE MÁQUINAS DE TURING") == 2


# Catálogo frente a los YAML


@pytest.mark.parametrize("entry", CATALOG, ids=[entry.file for entry in CATALOG])
def test_catalog_describes_exactly_the_states_and_markers_of_the_yaml(entry):
    machine, strings = loaded(entry)
    assert set(entry.states) == machine.states
    markers = machine.tape_alphabet - machine.input_alphabet - {BLANK}
    assert markers <= set(entry.symbols) <= machine.tape_alphabet - {BLANK}
    mentioned = set(re.findall(r"\bq\d+\b", " ".join([*entry.phases, *entry.states.values(), entry.cache,
                                                         entry.halting, entry.outcome])))
    assert mentioned <= machine.states
    assert all(entry.admits(word) for word in strings)
    assert not entry.admits("x") and not entry.admits("2")


# Procesos reales


def test_menu_works_from_another_working_directory(tmp_path):
    keys = "\n".join([ADDITION, STRINGS, "3", ENTER, back_from_list(ADDITION), BACK, EXIT]) + "\n"
    completed = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--interactive"],
        input=keys, cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    assert (completed.returncode, completed.stderr) == (0, "")
    assert "Cinta final:   101100" in completed.stdout
    assert completed.stdout.rstrip().endswith("Hasta luego.")


@pytest.mark.skipif(sys.platform == "win32", reason="SIGINT no se puede enviar así a un proceso en Windows")
def test_real_ctrl_c_exits_with_code_130_and_no_traceback():
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "main.py"), "--interactive"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
    )
    for line in process.stdout:
        if line.startswith("5. Salir"):
            break
    process.send_signal(signal.SIGINT)
    out, err = process.communicate(timeout=60)
    assert process.returncode == 130
    assert err == "" and "Traceback" not in out
    assert out.rstrip().endswith("Interrumpido con Ctrl+C: el simulador se cierra.")


def test_reported_walkthrough_in_a_real_process(tmp_path):
    """Recorrido del informe de uso: «aabbbb» desde la lista y «aab» como cadena nueva, con ENTER tras cada una."""
    keys = [RECOGNIZER, STRINGS, "4", ENTER, back_from_list(RECOGNIZER), NEW, "aab", ENTER, BACK, EXIT]
    completed = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--interactive"],
        input="\n".join(keys) + "\n", cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    out = completed.stdout
    assert (completed.returncode, completed.stderr) == (0, "")
    assert "Traceback" not in out and "Ver información" not in out
    assert out.count("A. Máquina: Reconocedora aⁿbⁿ") == 1
    runs = simulations(out)
    assert [word for word, _ in runs] == ["aabbbb", "aab"]
    verdicts = [sections["VEREDICTO FINAL"] for _, sections in runs]
    assert [verdict[0].strip() for verdict in verdicts] == ["REJECTED — CADENA RECHAZADA"] * 2
    assert [verdict[3] for verdict in verdicts] == ["Pasos realizados: 12", "Pasos realizados: 7"]
    after_pause = out.split(PAUSE)
    assert len(after_pause) == 3
    assert after_pause[1].lstrip("\n").startswith("CADENAS DISPONIBLES — Reconocedora aⁿbⁿ")
    assert after_pause[2].lstrip("\n").startswith(f"{RULE}\n{'MÁQUINA SELECCIONADA'.center(len(RULE)).rstrip()}")
    assert out.rstrip().endswith("Hasta luego.")

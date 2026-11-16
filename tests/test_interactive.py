"""Menú interactivo: navegación, ficha técnica, ejecución individual, validación y equivalencia con --machine.

La entrada del usuario se simula con ``Keyboard``, que entrega líneas en orden
y lanza ``EOFError`` cuando se agotan (como ``input``). Los reportes del menú se
comparan con la salida real de ``main.run`` para las mismas cadenas.
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
from src.cli.interactive_menu import ADDED, EXIT_INTERRUPTED, PREDEFINED, run_menu
from src.cli.machine_catalog import CATALOG
from src.input.machine_parser import parse_machine
from src.input.yaml_loader import load_yaml
from src.model.transition import BLANK
from src.output.machine_formatter import format_delta_table, formal_components
from src.utils.notation import blank_glyph

ROOT = Path(__file__).resolve().parents[1]
RECOGNIZER, INCREMENT, REVERSE, ADDITION = "1", "2", "3", "4"
EXIT = "5"
STRINGS, NEW, INFO, BACK = "1", "2", "3", "4"
"""Opciones del submenú de una máquina."""


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


def menu_reports(out):
    """Reportes del menú: {cadena: líneas del reporte sin el encabezado}."""
    reports = {}
    for block in out.split("\n=== Cadena: ")[1:]:
        lines = block.split("\n\nResumen de la ejecución:")[0].splitlines()
        word = re.fullmatch(r"(?:'(.*)'|ε \(cadena vacía\)) \(longitud \d+\) ===", lines[0]).group(1) or ""
        reports.setdefault(word, []).append(lines[1:])
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
    assert "=== Cadena" not in out and "MÁQUINA SELECCIONADA" not in out
    assert len(keyboard.prompts) == 2


def test_option_with_surrounding_spaces_is_accepted():
    _, out, _ = menu(f"  {INCREMENT} ", BACK, EXIT)
    assert "Alteradora — Incremento binario (transformer_binary_increment.yaml)" in out


@pytest.mark.parametrize(("option", "entry"), list(zip("1234", CATALOG)))
def test_selecting_a_machine_shows_its_sheet_without_running_any_string(option, entry):
    machine, _ = loaded(entry)
    blank = blank_glyph(machine)
    _, out, _ = menu(option, BACK, EXIT)
    lines = out.splitlines()
    assert "=== Cadena" not in out
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


def test_information_option_reprints_the_sheet_without_simulating():
    _, out, _ = menu(REVERSE, INFO, BACK, EXIT)
    assert out.count("A. Máquina: Inversión de cadenas") == 2
    assert "=== Cadena" not in out


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
        _, out, _ = menu(option, STRINGS, str(number), back_from_list(option), BACK, EXIT)
        reports = menu_reports(out)
        assert list(reports) == [word]
        assert reports[word] == [expected[word]]
        assert out.count("Resumen de la ejecución:") == 1


def test_report_shows_every_id_and_the_rule_applied_at_each_step():
    _, out, _ = menu(INCREMENT, STRINGS, "3", back_from_list(INCREMENT), BACK, EXIT)
    report = menu_reports(out)["11111"][0]
    start = report.index("Descripciones instantáneas (ID_0 a ID_12):")
    rows = report[start + 2:]
    assert [int(row.split()[0]) for row in rows] == list(range(13))
    assert rows[0].split()[1:] == ["[q0,B]11111", "—"]
    assert rows[-1] == "    12  [q2,B]100000  δ([q1, 1], B) = ([q2, B], 1, S)"
    assert "Cinta final:   100000" in report and "cabezal   ^" in report


def test_menu_strings_are_simulated_by_the_generic_engine(monkeypatch):
    calls = []
    real = interactive.simulate

    def spy(machine, word, max_steps):
        calls.append((machine.initial_state, len(machine.transitions), word, max_steps))
        return real(machine, word, max_steps)

    monkeypatch.setattr(interactive, "simulate", spy)
    menu(ADDITION, NEW, "1001#11", STRINGS, "1", back_from_list(ADDITION, 1), BACK, EXIT, max_steps=500)
    assert calls == [("q0", 57, "1001#11", 500), ("q0", 57, "1011#0110", 500)]


def test_max_steps_reaches_the_engine_and_limit_is_not_a_rejection():
    _, out, _ = menu(RECOGNIZER, STRINGS, "2", back_from_list(RECOGNIZER), BACK, EXIT, max_steps=30)
    report = menu_reports(out)["aaaabbbb"][0]
    assert report[0] == "Resultado:     LIMIT_EXCEEDED (sin veredicto: se alcanzó el límite de pasos, no es un rechazo)"


# Cadenas nuevas


def test_new_string_is_validated_added_and_run_immediately():
    _, out, _ = menu(INCREMENT, NEW, "0111", BACK, EXIT)
    assert "Alfabeto permitido: {0, 1}" in out
    assert "'0111' se agregó a la lista de esta sesión" in out
    report = menu_reports(out)["0111"][0]
    assert "Cinta final:   1000" in report


def test_new_strings_keep_leading_zeros():
    _, out, _ = menu(REVERSE, NEW, "00110", BACK, EXIT)
    assert "Cinta final:   01100" in menu_reports(out)["00110"][0]


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
    assert "=== Cadena" not in out
    assert keyboard.prompts.count("Ingrese una cadena: ") == 1


def test_retry_after_an_invalid_string():
    _, out, keyboard = menu(ADDITION, NEW, "10#", "1", "10#1", BACK, EXIT)
    assert keyboard.prompts.count("Ingrese una cadena: ") == 2
    assert list(menu_reports(out)) == ["10#1"]
    assert "Cinta final:   11" in menu_reports(out)["10#1"][0]


@pytest.mark.parametrize(("option", "admitted"), [(RECOGNIZER, True), (REVERSE, True), (INCREMENT, False)])
def test_empty_line_is_the_empty_string_only_where_the_domain_admits_it(option, admitted):
    code, out, _ = menu(option, NEW, "")
    assert code == 0
    assert ("Deje la línea vacía para ingresar la cadena vacía (ε)." in out) is admitted
    assert ("ε (cadena vacía) se agregó" in out) is admitted
    assert list(menu_reports(out)) == ([""] if admitted else [])


def test_a_digit_typed_as_an_option_is_never_taken_as_a_string():
    _, out, _ = menu("1", "1", "1", back_from_list(RECOGNIZER), BACK, EXIT)
    assert list(menu_reports(out)) == ["aaabbb"]
    assert "se agregó" not in out


def test_session_strings_persist_when_returning_to_the_main_menu():
    _, out, _ = menu(REVERSE, NEW, "0011", BACK, REVERSE, STRINGS, back_from_list(REVERSE, 1), BACK, EXIT)
    assert listing(out, "Inversión de cadenas")[-2:] == [("'0011'", ADDED), ("Regresar", "")]


def test_repeated_strings_are_not_duplicated_in_the_list():
    added = back_from_list(INCREMENT)
    _, out, _ = menu(INCREMENT, NEW, "10101", NEW, "0011", NEW, "0011", STRINGS, back_from_list(INCREMENT, 1), BACK, EXIT)
    assert "'10101' ya está en la lista (n.º 1); no se duplica." in out
    assert f"'0011' ya está en la lista (n.º {added}); no se duplica." in out
    assert [text for text, _ in listing(out, "Incremento binario")].count("'0011'") == 1
    assert len(menu_reports(out)["0011"]) == 2


def test_session_strings_do_not_leak_between_machines():
    _, out, _ = menu(INCREMENT, NEW, "0110", BACK, REVERSE, STRINGS, back_from_list(REVERSE), BACK, EXIT)
    assert ("'0110'", ADDED) not in listing(out, "Inversión de cadenas")


def test_session_never_writes_the_yaml_files():
    before = {entry.file: entry.path.read_bytes() for entry in CATALOG}
    menu(INCREMENT, NEW, "0110", BACK, ADDITION, NEW, "1#1", BACK, EXIT)
    assert {entry.file: entry.path.read_bytes() for entry in CATALOG} == before


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
    keys = "\n".join([ADDITION, STRINGS, "3", back_from_list(ADDITION), BACK, EXIT]) + "\n"
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

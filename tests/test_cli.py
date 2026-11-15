"""CLI: argumentos, carga del YAML, ejecución de todas las cadenas y códigos de salida."""

import subprocess
import sys
from pathlib import Path

import pytest

import main

ROOT = Path(__file__).resolve().parents[1]
LAB10 = ROOT / "machines" / "examples" / "basic_machine.yaml"
STATEMENT = ROOT / "tests" / "fixtures" / "statement_example_mt_1.yaml"


def run_cli(capsys, *args):
    code = main.main([str(arg) for arg in args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_runs_every_string_in_file_order(capsys):
    code, out, err = run_cli(capsys, "--machine", LAB10)
    assert (code, err) == (main.EXIT_OK, "")
    headers = [line for line in out.splitlines() if line.startswith("=== Cadena")]
    assert headers == [
        "=== Cadena 1 de 5: 'aab#aab' (longitud 7) ===",
        "=== Cadena 2 de 5: 'ab#ab' (longitud 5) ===",
        "=== Cadena 3 de 5: 'abbababa#aba' (longitud 12) ===",
        "=== Cadena 4 de 5: 'abb#aab' (longitud 7) ===",
        "=== Cadena 5 de 5: '#' (longitud 1) ===",
    ]
    assert "=== Resumen ===" in out


def test_prints_the_formal_description_of_the_machine(capsys):
    _, out, _ = run_cli(capsys, "--machine", LAB10)
    assert "  Q  = {0, 1, 2, 3, 4, 5}" in out
    assert "  Σ  = {#, a, b}" in out
    assert "  F  = {5}" in out
    assert "  δ  = 20 reglas" in out


def test_header_lists_every_rule_of_delta_in_yaml_order(capsys):
    """Observación L-1 del Gate 02: la tabla δ completa es visible en la salida, no solo su tamaño."""
    _, out, _ = run_cli(capsys, "--machine", ROOT / "machines" / "transformer_binary_increment.yaml")
    lines = out.splitlines()
    start = lines.index("  δ  = 6 reglas, en el orden del YAML:")
    assert lines[start + 1:start + 8] == [
        "    1. δ([q0, B], 0) = ([q0, B], 0, R)",
        "    2. δ([q0, B], 1) = ([q0, B], 1, R)",
        "    3. δ([q0, B], B) = ([q1, 1], B, L)",
        "    4. δ([q1, 1], 1) = ([q1, 1], 0, L)",
        "    5. δ([q1, 1], 0) = ([q2, B], 1, S)",
        "    6. δ([q1, 1], B) = ([q2, B], 1, S)",
        "Cadenas: 4 · límite de pasos por cadena: 10000",
    ]


def test_header_numbers_all_rules_with_aligned_indices(capsys):
    _, out, _ = run_cli(capsys, "--machine", LAB10)
    listed = [line for line in out.splitlines() if line.startswith("  ") and ". δ(" in line]
    assert len(listed) == 20
    assert listed[0] == "     1. δ([0, B], a) = ([1, a], B, R)"
    assert listed[-1].startswith("    20. δ(")


def test_help_describes_the_options(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main.main(["--help"])
    out = capsys.readouterr().out
    assert exit_info.value.code == 0
    assert "--machine ARCHIVO" in out and "--max-steps N" in out


def test_missing_machine_argument_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main.main([])
    assert exit_info.value.code == 2
    assert "--machine" in capsys.readouterr().err


@pytest.mark.parametrize("value", ["0", "-3", "diez"])
def test_max_steps_must_be_a_positive_integer(capsys, value):
    with pytest.raises(SystemExit) as exit_info:
        main.main(["--machine", str(LAB10), "--max-steps", value])
    assert exit_info.value.code == 2
    assert "entero positivo" in capsys.readouterr().err


def test_missing_file_is_an_input_error(capsys, tmp_path):
    code, out, err = run_cli(capsys, "--machine", tmp_path / "missing.yaml")
    assert (code, out) == (main.EXIT_INPUT_ERROR, "")
    assert err.startswith("error: ") and "no se puede leer" in err


def test_invalid_machine_reports_every_problem_without_simulating(capsys):
    code, out, err = run_cli(capsys, "--machine", STATEMENT)
    assert (code, out) == (main.EXIT_INPUT_ERROR, "")
    assert "tape_alphabet: debe incluir los símbolos de alphabet" in err
    assert "simulation_strings[0]" in err
    assert "REJECTED" not in err


def test_max_steps_is_passed_to_the_engine(capsys):
    code, out, _ = run_cli(capsys, "--machine", LAB10, "--max-steps", "5")
    assert code == main.EXIT_OK
    assert "límite de pasos por cadena: 5" in out
    assert out.count("Resultado:     LIMIT_EXCEEDED") == 4  # '#' se acepta en 2 pasos


def test_running_as_a_script_writes_utf8(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--machine", str(LAB10)],
        capture_output=True,
        cwd=tmp_path,
    )
    out = completed.stdout.decode("utf-8")
    assert completed.returncode == 0
    assert "δ([0, B], a) = ([1, a], B, R)" in out
    assert "Resultado:     ACCEPTED (aceptada)" in out


# --- Integración YAML → parser → motor → traza → salida estándar -----------------------------

RECOGNIZER = ROOT / "machines" / "recognizer_anbn.yaml"
TRANSFORMER = ROOT / "machines" / "transformer_binary_increment.yaml"

RULE = """\
- params:
    initial_state: {state}
    mem_cache_value:
    tape_input: {read}
  output:
    final_state: {next_state}
    mem_cache_value:
    tape_output: {write}
    tape_displacement: {move}
"""


def write_machine(tmp_path, *, states="[s, f]", final="f", alphabet="[a]", tape="[a, X, null]",
                  rules=(), strings="[a]"):
    delta = "\n" + "".join(RULE.format(**rule) for rule in rules) if rules else " []\n"
    text = (
        f"q_states:\n  q_list: {states}\n  initial: s\n  final: {final}\n"
        f"alphabet: {alphabet}\ntape_alphabet: {tape}\n"
        f"delta:{delta}simulation_strings: {strings}\n"
    )
    path = tmp_path / "machine.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def summary_rows(out):
    lines = out.splitlines()
    return [line.split() for line in lines[lines.index("=== Resumen ===") + 2:]]


def id_rows(out, number):
    """Filas de la tabla de IDs de la cadena ``number`` (sin el encabezado)."""
    lines = out.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(f"=== Cadena {number} de"))
    header = next(i for i in range(start, len(lines)) if lines[i].strip().startswith("Paso  ID"))
    rows = []
    for line in lines[header + 1:]:
        if not line.startswith("  "):
            break
        rows.append(line.split(maxsplit=2))
    return rows


def test_recognizer_end_to_end(capsys):
    code, out, err = run_cli(capsys, "--machine", RECOGNIZER)
    assert (code, err) == (main.EXIT_OK, "")
    assert summary_rows(out) == [
        ["1", "aaabbb", "6", "ACCEPTED", "25", "XXXYYY"],
        ["2", "aaaabbbb", "8", "ACCEPTED", "41", "XXXXYYYY"],
        ["3", "aaabb", "5", "REJECTED", "17", "XXXYY"],
        ["4", "aabbbb", "6", "REJECTED", "12", "XXYYbb"],
    ]
    assert "ID final:      XXXYYYB[q4,B]B" in out
    assert "ID final:      XXYY[q3,B]bb" in out


def test_transformer_end_to_end(capsys):
    code, out, _ = run_cli(capsys, "--machine", TRANSFORMER)
    assert code == main.EXIT_OK
    assert summary_rows(out) == [
        ["1", "10101", "5", "ACCEPTED", "8", "10110"],
        ["2", "11011", "5", "ACCEPTED", "9", "11100"],
        ["3", "11111", "5", "ACCEPTED", "12", "100000"],
        ["4", "10000", "5", "ACCEPTED", "7", "10001"],
    ]
    assert "Cinta final:   100000" in out
    assert "δ([q1, 1], B) = ([q2, B], 1, S)" in out


@pytest.mark.parametrize(("path", "number", "steps"), [(RECOGNIZER, 1, 25), (RECOGNIZER, 3, 17), (TRANSFORMER, 3, 12)])
def test_every_id_is_printed_once_and_in_order(capsys, path, number, steps):
    _, out, _ = run_cli(capsys, "--machine", path)
    rows = id_rows(out, number)
    assert [int(row[0]) for row in rows] == list(range(steps + 1))
    assert rows[0][2] == "—"
    assert all(row[2].startswith("δ(") for row in rows[1:])


def test_transformer_ids_show_the_cache_and_the_negative_cell(capsys):
    _, out, _ = run_cli(capsys, "--machine", TRANSFORMER)
    rows = id_rows(out, 3)
    assert [row[1] for row in rows[-3:]] == ["[q1,1]10000", "[q1,1]B00000", "[q2,B]100000"]


def test_input_strings_are_preserved_and_file_is_not_modified(capsys):
    before = TRANSFORMER.read_bytes()
    _, out, _ = run_cli(capsys, "--machine", TRANSFORMER)
    headers = [line for line in out.splitlines() if line.startswith("=== Cadena")]
    assert [h.split("'")[1] for h in headers] == ["10101", "11011", "11111", "10000"]
    assert TRANSFORMER.read_bytes() == before


def test_successive_runs_are_independent_and_identical(capsys):
    first = run_cli(capsys, "--machine", RECOGNIZER)
    run_cli(capsys, "--machine", TRANSFORMER)
    second = run_cli(capsys, "--machine", RECOGNIZER)
    assert first == second


def test_machine_without_transitions_rejects_without_moving(capsys, tmp_path):
    path = write_machine(tmp_path, strings="[a, aa]")
    code, out, _ = run_cli(capsys, "--machine", path)
    assert code == main.EXIT_OK
    assert "  δ  = 0 reglas" in out
    assert [row[3:5] for row in summary_rows(out)] == [["REJECTED", "0"], ["REJECTED", "0"]]


def test_limit_exceeded_is_reported_separately_from_rejection(capsys, tmp_path):
    loop = {"state": "s", "read": "a", "next_state": "s", "write": "a", "move": "S"}
    path = write_machine(tmp_path, rules=[loop])
    code, out, _ = run_cli(capsys, "--machine", path, "--max-steps", "7")
    assert code == main.EXIT_OK
    assert "Resultado:     LIMIT_EXCEEDED (sin veredicto: se alcanzó el límite de pasos, no es un rechazo)" in out
    assert summary_rows(out) == [["1", "a", "1", "LIMIT_EXCEEDED", "7", "a"]]
    assert "REJECTED" not in out
    assert len(id_rows(out, 1)) == 8


def test_unicode_symbols_and_states_are_printed(capsys, tmp_path):
    rule = {"state": "s", "read": "ñ", "next_state": "fín", "write": "λ", "move": "R"}
    path = write_machine(tmp_path, states="[s, fín]", final="fín", alphabet="[ñ]", tape="[ñ, λ, null]",
                         rules=[rule], strings="[ñ]")
    code, out, _ = run_cli(capsys, "--machine", path)
    assert code == main.EXIT_OK
    assert "δ([s, B], ñ) = ([fín, B], λ, R)" in out
    assert "ID final:      λ[fín,B]B" in out


def test_symbol_b_switches_the_blank_glyph(capsys, tmp_path):
    rule = {"state": "s", "read": "a", "next_state": "f", "write": "B", "move": "R"}
    path = write_machine(tmp_path, tape="[a, B, null]", rules=[rule])
    _, out, _ = run_cli(capsys, "--machine", path)
    assert "  B  = □ (blanco)" in out
    assert "    1. δ([s, □], a) = ([f, □], B, R)" in out
    assert "ID final:      B[f,□]□" in out


def test_empty_string_list_is_not_an_error(capsys, tmp_path):
    code, out, _ = run_cli(capsys, "--machine", write_machine(tmp_path, strings="[]"))
    assert code == main.EXIT_OK
    assert "El archivo no contiene cadenas en simulation_strings." in out


def test_empty_input_string_is_simulated(capsys, tmp_path):
    accept = {"state": "s", "read": "null", "next_state": "f", "write": "X", "move": "S"}
    code, out, _ = run_cli(capsys, "--machine", write_machine(tmp_path, rules=[accept], strings="['']"))
    assert code == main.EXIT_OK
    assert "=== Cadena 1 de 1: ε (cadena vacía) (longitud 0) ===" in out
    assert "Cinta final:   X" in out


def test_yaml_syntax_error_is_an_input_error(capsys, tmp_path):
    path = tmp_path / "broken.yaml"
    path.write_text("q_states:\n  q_list: [s\n", encoding="utf-8")
    code, out, err = run_cli(capsys, "--machine", path)
    assert (code, out) == (main.EXIT_INPUT_ERROR, "")
    assert "YAML inválido" in err


def test_directory_path_is_an_input_error(capsys, tmp_path):
    code, _, err = run_cli(capsys, "--machine", tmp_path)
    assert code == main.EXIT_INPUT_ERROR and "no se puede leer" in err


def test_both_demo_machines_run_as_scripts(tmp_path):
    for path, expected in [(RECOGNIZER, ["4", "aabbbb", "6", "REJECTED", "12", "XXYYbb"]),
                           (TRANSFORMER, ["3", "11111", "5", "ACCEPTED", "12", "100000"])]:
        completed = subprocess.run([sys.executable, str(ROOT / "main.py"), "--machine", str(path)],
                                   capture_output=True, cwd=tmp_path)
        assert completed.returncode == 0
        assert expected in summary_rows(completed.stdout.decode("utf-8"))

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

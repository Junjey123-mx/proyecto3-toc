"""Integración de extremo a extremo: YAML → CLI → salida estándar, contrastada con oráculos.

Las pruebas ejecutan ``main.py`` como proceso aparte (``sys.executable``) desde un
directorio de trabajo temporal y comparan lo impreso con valores obtenidos sin el
simulador: la definición de L = {aⁿbⁿ | n ≥ 1}, la aritmética binaria de Python,
``w[::-1]`` y una reproducción de δ leída directamente del YAML con
``yaml.safe_load``. Al final se comprueba que el README describa el repositorio
real: enlaces internos, rutas, secciones citadas, secuencia del video y conteo de
pruebas.
"""

import itertools
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from src.input.machine_parser import parse_machine
from src.input.machine_validator import validate_machine
from src.input.yaml_loader import load_yaml
from src.simulator.engine import simulate
from src.simulator.trace import build_trace

ROOT = Path(__file__).resolve().parents[1]
RECOGNIZER = ROOT / "machines" / "recognizer_anbn.yaml"
TRANSFORMER = ROOT / "machines" / "transformer_binary_increment.yaml"
REVERSE = ROOT / "machines" / "transformer_binary_reverse.yaml"
ADDITION = ROOT / "machines" / "transformer_binary_addition.yaml"
README = ROOT / "README.md"
DEMOS = {
    RECOGNIZER: ["aaabbb", "aaaabbbb", "aaabb", "aabbbb"],
    TRANSFORMER: ["10101", "11011", "11111", "10000"],
    REVERSE: ["10110", "11001", "10000", "11100"],
    ADDITION: ["1011#0110", "1111#0001", "10101#10111", "10000#00001"],
}

HEADER = re.compile(r"Cadena \d+ de \d+: (?:'(.*)'|ε \(cadena vacía\)) \(longitud (\d+)\) ===")
FIELD = re.compile(r"(Resultado|Motivo|Pasos|Estado final|Caché final|Cabezal final|Cinta final|ID final):\s+(.*)")


# --- Oráculos: no usan ninguna parte del simulador ------------------------------------------

def in_anbn(word):
    n = len(word) // 2
    return n >= 1 and word == "a" * n + "b" * n


def increment(word):
    """value₂(w) + 1 en binario, con al menos |w| bits (conserva los ceros a la izquierda)."""
    return format(int(word, 2) + 1, f"0{len(word)}b")


def reverse(word):
    return word[::-1]


def binary_sum(word):
    """A + B con max(|A|, |B|) bits como mínimo; A y B se leen de ``A#B`` solo aquí."""
    a, b = word.split("#")
    return format(int(a, 2) + int(b, 2), f"0{max(len(a), len(b))}b")


ORACLES = {TRANSFORMER: increment, REVERSE: reverse, ADDITION: binary_sum}


def raw_machine(path):
    """δ, q0 y F leídos del YAML sin el parser del proyecto."""
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    moves = {"L": -1, "R": 1, "S": 0}
    delta = {}
    for rule in document["delta"]:
        p, o = rule["params"], rule["output"]
        key = (p["initial_state"], p["mem_cache_value"], p["tape_input"])
        delta[key] = (o["final_state"], o["mem_cache_value"], o["tape_output"], moves[o["tape_displacement"]])
    return delta, document["q_states"]["initial"], {document["q_states"]["final"]}


# --- Ejecución y lectura de la salida de la CLI ----------------------------------------------

def run_cli(cwd, machine, *args):
    completed = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--machine", str(machine), *map(str, args)],
        capture_output=True, cwd=cwd, timeout=120,
    )
    return completed.returncode, completed.stdout.decode("utf-8"), completed.stderr.decode("utf-8")


def parse_output(out):
    """Reportes por cadena (campos, longitud y tabla de IDs) y filas del resumen, en orden."""
    body, summary = out.split("\n=== Resumen ===\n")
    reports = []
    for chunk in body.split("\n=== Cadena ")[1:]:
        lines = chunk.splitlines()
        header = HEADER.fullmatch("Cadena " + lines[0])
        report = dict(m.groups() for m in map(FIELD.fullmatch, lines) if m)
        table = next(i for i, line in enumerate(lines) if line.startswith("Descripciones instantáneas"))
        report.update(
            word=header[1] or "",
            length=int(header[2]),
            last_id=int(lines[table].split("ID_")[-1].rstrip("):")),
            ids=[row.split(maxsplit=2) for row in lines[table + 2:] if row.startswith("  ")],
        )
        reports.append(report)
    rows = [line.split(maxsplit=5) for line in summary.splitlines()[1:]]
    return reports, rows


def write_yaml(tmp_path, name, document):
    path = tmp_path / name
    path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def with_strings(tmp_path, machine, strings):
    """Copia temporal de ``machine`` con otra lista ``simulation_strings``."""
    document = yaml.safe_load(machine.read_text(encoding="utf-8"))
    document["simulation_strings"] = strings
    return write_yaml(tmp_path, machine.name, document)


# --- Ocho ejecuciones de la demostración ------------------------------------------------------

def test_recognizer_demo_agrees_with_the_definition_of_the_language(tmp_path):
    code, out, err = run_cli(tmp_path, RECOGNIZER)
    assert (code, err) == (0, "")
    reports, _ = parse_output(out)
    assert [r["word"] for r in reports] == DEMOS[RECOGNIZER]
    for report in reports:
        word, n = report["word"], len(report["word"]) // 2
        assert report["length"] == len(word) >= 5
        if in_anbn(word):
            assert report["Resultado"] == "ACCEPTED (aceptada)"
            assert report["Pasos"] == str(2 * n * n + 2 * n + 1)
            assert report["Cinta final"] == "X" * n + "Y" * n
        else:
            assert report["Resultado"] == "REJECTED (rechazada)"
    verdicts = [r["Resultado"].split()[0] for r in reports]
    assert verdicts.count("ACCEPTED") == 2 and verdicts.count("REJECTED") == 2


def test_transformer_demo_writes_the_binary_successor(tmp_path):
    code, out, err = run_cli(tmp_path, TRANSFORMER)
    assert (code, err) == (0, "")
    reports, _ = parse_output(out)
    assert [r["word"] for r in reports] == DEMOS[TRANSFORMER]
    assert [r["Cinta final"] for r in reports] == ["10110", "11100", "100000", "10001"]
    for report in reports:
        assert report["length"] == len(report["word"]) >= 5
        assert report["Resultado"] == "ACCEPTED (aceptada)"
        assert report["Cinta final"] == increment(report["word"])


@pytest.mark.parametrize("machine", [REVERSE, ADDITION], ids=["inversión", "suma"])
def test_new_transformer_demos_agree_with_their_oracles(tmp_path, machine):
    code, out, err = run_cli(tmp_path, machine)
    assert (code, err) == (0, "")
    reports, rows = parse_output(out)
    assert [r["word"] for r in reports] == DEMOS[machine]
    for report, row in zip(reports, rows):
        assert report["length"] == len(report["word"]) >= 5
        assert report["Resultado"] == "ACCEPTED (aceptada)"
        assert report["Cinta final"] == row[5] == ORACLES[machine](report["word"])
        assert not set(report["Cinta final"]) & {"#", "*", "o", "i"}


@pytest.mark.parametrize("word", DEMOS[TRANSFORMER])
def test_transformer_logical_tape_holds_exactly_the_successor(word):
    machine, _ = parse_machine(load_yaml(TRANSFORMER))
    expected = increment(word)
    start = len(word) - len(expected)  # -1 si hubo desbordamiento
    assert dict(simulate(machine, word).final.tape) == {start + i: bit for i, bit in enumerate(expected)}


@pytest.mark.parametrize(("machine", "word"), [(m, w) for m, words in DEMOS.items() for w in words])
def test_every_id_is_one_application_of_the_yaml_delta(machine, word):
    """Reproduce cada ID_k+1 desde ID_k con la δ leída del YAML, sin usar el motor."""
    model, strings = parse_machine(load_yaml(machine))
    validate_machine(model, strings)
    result = simulate(model, word)
    trace = build_trace(result)
    assert len(result.configurations) == len(trace.entries) == result.steps + 1 == trace.steps + 1

    delta, initial, final = raw_machine(machine)
    state, cache, head, tape = initial, None, 0, dict(enumerate(word))
    assert (trace.entries[0].state, trace.entries[0].cache, trace.entries[0].head) == (state, cache, head)
    assert trace.entries[0].applied is None and dict(trace.entries[0].tape) == tape
    for entry in trace.entries[1:]:
        state, cache, write, move = delta[(state, cache, tape.get(head))]
        if write is None:
            tape.pop(head, None)
        else:
            tape[head] = write
        head += move
        assert (entry.state, entry.cache, entry.head, dict(entry.tape)) == (state, cache, head, tape)

    stuck = (state, cache, tape.get(head)) not in delta
    assert result.outcome.value == ("ACCEPTED" if state in final else "REJECTED")
    assert state in final or stuck


# --- Coherencia del reporte para los tres resultados posibles --------------------------------

def test_report_fields_table_and_summary_agree_for_every_outcome(tmp_path):
    code, out, _ = run_cli(tmp_path, RECOGNIZER, "--max-steps", 30)
    assert code == 0
    delta, _, _ = raw_machine(RECOGNIZER)
    assert f"  δ  = {len(delta)} reglas" in out
    assert "  Q  = {q0, q1, q2, q3, q4}" in out and "  F  = {q4}" in out
    reports, rows = parse_output(out)
    reasons = {
        "ACCEPTED": "alcanzó el estado final 'q4'",
        "REJECTED": "no hay regla para el estado",
        "LIMIT_EXCEEDED": "se aplicaron 30 transiciones y la máquina aún no se detiene",
    }
    assert [r["Resultado"].split()[0] for r in reports] == ["ACCEPTED", "LIMIT_EXCEEDED", "REJECTED", "REJECTED"]
    for number, (report, row) in enumerate(zip(reports, rows), start=1):
        outcome, steps = report["Resultado"].split()[0], int(report["Pasos"])
        assert report["Motivo"].startswith(reasons[outcome])
        assert report["last_id"] == steps == len(report["ids"]) - 1
        assert [int(r[0]) for r in report["ids"]] == list(range(steps + 1))
        assert report["ids"][0][2] == "—" and all(r[2].startswith("δ(") for r in report["ids"][1:])
        assert report["ids"][-1][1] == report["ID final"]
        assert f"[{report['Estado final']},{report['Caché final']}]" in report["ID final"]
        assert row == [str(number), report["word"], str(report["length"]), outcome, str(steps), report["Cinta final"]]
    assert reports[1]["Pasos"] == "30"


@pytest.mark.parametrize(("machine", "limit", "expected"), [
    (RECOGNIZER, 16, ["LIMIT_EXCEEDED", "LIMIT_EXCEEDED", "LIMIT_EXCEEDED", "REJECTED"]),
    (RECOGNIZER, 17, ["LIMIT_EXCEEDED", "LIMIT_EXCEEDED", "REJECTED", "REJECTED"]),
    (RECOGNIZER, 24, ["LIMIT_EXCEEDED", "LIMIT_EXCEEDED", "REJECTED", "REJECTED"]),
    (RECOGNIZER, 25, ["ACCEPTED", "LIMIT_EXCEEDED", "REJECTED", "REJECTED"]),
    (RECOGNIZER, 40, ["ACCEPTED", "LIMIT_EXCEEDED", "REJECTED", "REJECTED"]),
    (RECOGNIZER, 41, ["ACCEPTED", "ACCEPTED", "REJECTED", "REJECTED"]),
    (TRANSFORMER, 11, ["ACCEPTED", "ACCEPTED", "LIMIT_EXCEEDED", "ACCEPTED"]),
    (TRANSFORMER, 12, ["ACCEPTED", "ACCEPTED", "ACCEPTED", "ACCEPTED"]),
    (REVERSE, 29, ["LIMIT_EXCEEDED"] * 4),
    (REVERSE, 30, ["ACCEPTED"] * 4),
    (ADDITION, 73, ["ACCEPTED", "ACCEPTED", "LIMIT_EXCEEDED", "LIMIT_EXCEEDED"]),
    (ADDITION, 84, ["ACCEPTED", "ACCEPTED", "LIMIT_EXCEEDED", "ACCEPTED"]),
    (ADDITION, 99, ["ACCEPTED"] * 4),
])
def test_halting_exactly_at_the_step_limit_is_a_verdict(tmp_path, machine, limit, expected):
    """Regresión D-4 del Gate 01: detenerse justo en ``max_steps`` acepta o rechaza; no es un límite."""
    code, out, _ = run_cli(tmp_path, machine, "--max-steps", limit)
    assert code == 0
    assert [row[3] for row in parse_output(out)[1]] == expected


def test_strings_do_not_share_tape_cache_or_results(tmp_path):
    for machine, words in DEMOS.items():
        reference = {r["word"]: r for r in parse_output(run_cli(tmp_path, machine)[1])[0]}
        reordered = [*reversed(words), words[0], words[2], words[0]]
        code, out, _ = run_cli(tmp_path, with_strings(tmp_path, machine, reordered))
        assert code == 0
        reports, _ = parse_output(out)
        assert [r["word"] for r in reports] == reordered
        assert all(report == reference[report["word"]] for report in reports)


def short_words(alphabet, lengths):
    return ["".join(p) for n in lengths for p in itertools.product(alphabet, repeat=n)]


def test_cli_agrees_with_the_oracles_on_every_short_string(tmp_path):
    operands = short_words("01", range(1, 4))
    sweeps = [
        (RECOGNIZER, short_words("ab", range(0, 9))),
        (TRANSFORMER, short_words("01", range(1, 10))),
        (REVERSE, short_words("01", range(0, 9))),
        (ADDITION, [f"{a}#{b}" for a in operands for b in operands]),
    ]
    for machine, words in sweeps:
        code, out, err = run_cli(tmp_path, with_strings(tmp_path, machine, words))
        assert (code, err) == (0, "")
        rows = parse_output(out)[1]
        assert [row[1] for row in rows] == [word or "ε" for word in words]
        for word, row in zip(words, rows):
            if machine == RECOGNIZER:
                assert row[3] == ("ACCEPTED" if in_anbn(word) else "REJECTED"), word
            else:
                assert (row[3], row[5]) == ("ACCEPTED", ORACLES[machine](word) or "(cinta en blanco)"), word


def test_final_states_are_terminal_even_with_outgoing_rules(tmp_path):
    rules = [("s", None, "a", "f", None, "X", "R"), ("f", None, None, "s", None, "a", "L")]
    document = {
        "q_states": {"q_list": ["s", "f"], "initial": "s", "final": "f"},
        "alphabet": ["a"],
        "tape_alphabet": ["a", "X", None],
        "delta": [
            {"params": {"initial_state": q, "mem_cache_value": c, "tape_input": r},
             "output": {"final_state": p, "mem_cache_value": d, "tape_output": w, "tape_displacement": m}}
            for q, c, r, p, d, w, m in rules
        ],
        "simulation_strings": ["a", "aa"],
    }
    code, out, _ = run_cli(tmp_path, write_yaml(tmp_path, "terminal.yaml", document))
    assert code == 0
    assert parse_output(out)[1] == [["1", "a", "1", "ACCEPTED", "1", "X"], ["2", "aa", "2", "ACCEPTED", "1", "Xa"]]


# --- Errores de entrada: se reportan como errores, nunca como rechazo ------------------------

SOURCE = TRANSFORMER.read_text(encoding="utf-8")
BROKEN = {
    "sintaxis": ("q_states:\n  q_list: [q0\n", "YAML inválido"),
    "clave_repetida": (SOURCE.replace("    tape_input: '0'\n", "    tape_input: '0'\n    tape_input: '1'\n", 1),
                       "clave repetida 'tape_input'"),
    "clave_faltante": (SOURCE.replace("delta:", "deltas:", 1), "falta la clave obligatoria 'delta'"),
    "desplazamiento": (SOURCE.replace("tape_displacement: S", "tape_displacement: X", 1),
                       "delta[4].output.tape_displacement: debe ser L, R o S, no 'X'"),
    "estado": (SOURCE.replace("final_state: q2", "final_state: q9", 1),
               "delta[4].output.final_state: 'q9' no pertenece a q_list"),
    "fuera_de_sigma": (SOURCE.replace("- '10000'", "- '10201'"),
                       "simulation_strings[3]: '10201' usa símbolos fuera de alphabet"),
}


@pytest.mark.parametrize("case", [*BROKEN, "inexistente"])
def test_input_errors_are_reported_with_their_location_and_never_simulated(tmp_path, case):
    if case == "inexistente":
        path, fragment = tmp_path / "missing.yaml", "no se puede leer"
    else:
        text, fragment = BROKEN[case]
        path = tmp_path / f"{case}.yaml"
        path.write_text(text, encoding="utf-8")
    code, out, err = run_cli(tmp_path, path)
    assert (code, out) == (1, "")
    assert err.startswith("error: ") and fragment in err
    assert not any(word in err for word in ("ACCEPTED", "REJECTED", "LIMIT_EXCEEDED"))


# --- Evidencia de la demostración ------------------------------------------------------------

@pytest.mark.parametrize("name", [machine.stem for machine in DEMOS])
def test_demonstration_evidence_matches_the_current_output(name):
    """``docs/evidence/`` guarda la salida real de las cuatro demostraciones; debe seguir siendo exacta."""
    code, out, err = run_cli(ROOT, f"machines/{name}.yaml")
    assert (code, err) == (0, "")
    assert out.replace("\r\n", "\n") == (ROOT / "docs" / "evidence" / f"{name}.txt").read_text(encoding="utf-8")


# --- Menú interactivo con la secuencia del video ---------------------------------------------

def test_video_key_sequence_of_the_readme_runs_the_eight_demonstrations(tmp_path):
    """La secuencia de teclas de README.md, §25.2, produce las ocho ejecuciones obligatorias y una cadena nueva."""
    text = README.read_text(encoding="utf-8")
    keys = re.search(r"Secuencia completa de teclas.*?```text\n(.+?)\n```", text, flags=re.DOTALL).group(1).split()
    completed = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--interactive"],
        input="\n".join(keys) + "\n", capture_output=True, cwd=tmp_path, timeout=120, encoding="utf-8",
    )
    assert (completed.returncode, completed.stderr) == (0, "")
    runs = re.findall(r"^=== Cadena: '(.*)' \(longitud \d+\) ===\nResultado:     (\w+)", completed.stdout, flags=re.MULTILINE)
    outputs = re.findall(r"^Cinta final:   (.*)$", completed.stdout, flags=re.MULTILINE)
    assert runs == [
        ("aaabbb", "ACCEPTED"), ("aaaabbbb", "ACCEPTED"), ("aaabb", "REJECTED"), ("aabbbb", "REJECTED"),
        *[(word, "ACCEPTED") for word in DEMOS[ADDITION]], ("101#11", "ACCEPTED"),
    ]
    assert outputs[4:] == [binary_sum(word) for word in [*DEMOS[ADDITION], "101#11"]]
    assert completed.stdout.rstrip().endswith("Hasta luego.")


# --- El README describe el repositorio real ----------------------------------------------------

RETIRED = {
    "docs/architecture.md", "docs/methodology.md", "docs/test_cases.md",
    "docs/handoff_gate_01_derek.md", "docs/handoff_gate_02_vernel.md",
}
"""Documentos integrados en el README y retirados del árbol; solo se citan como historial."""


def slug(heading):
    """Ancla de GitHub: minúsculas, sin puntuación, espacios convertidos en guiones."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def readme_headings(text):
    return [slug(heading) for heading in re.findall(r"^#{2,3} (.+)$", text, flags=re.MULTILINE)]


def test_readme_internal_links_resolve_to_unique_headings():
    text = README.read_text(encoding="utf-8")
    headings = readme_headings(text)
    assert len(headings) == len(set(headings))
    links = set(re.findall(r"\]\(#([^)]+)\)", text))
    assert links and links <= set(headings)


def test_readme_paths_exist_except_the_retired_documents():
    text = README.read_text(encoding="utf-8")
    paths = set(re.findall(r"`((?:machines|docs|src|tests)/[\w./-]+)`", text))
    assert {path for path in paths if not (ROOT / path).exists()} == RETIRED & paths
    assert not any((ROOT / path).exists() for path in RETIRED)
    assert "git show 6a27bab:docs/handoff_gate_01_derek.md" in text


def test_sections_cited_from_code_and_machines_exist_in_the_readme():
    text = README.read_text(encoding="utf-8")
    numbers = {re.match(r"(\d+(?:\.\d+)?)", heading).group(1)
               for heading in re.findall(r"^#{2,3} (\d+(?:\.\d+)?)\.? ", text, flags=re.MULTILINE)}
    cited = set()
    for path in [*ROOT.glob("machines/*.yaml"), *ROOT.glob("tests/*.py"), *ROOT.glob("tests/fixtures/*.yaml")]:
        source = path.read_text(encoding="utf-8")
        cited |= set(re.findall(r"README\.md\W{0,4}(?:\(sección |, §| §)(\d+(?:\.\d+)?)", source))
    assert cited and cited <= numbers


def test_readme_test_counts_match_the_collected_suite():
    collected = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        capture_output=True, cwd=ROOT, timeout=120, encoding="utf-8",
    ).stdout
    counts = {}
    for line in collected.splitlines():
        if "::" in line:
            name = Path(line.split("::")[0]).name
            counts[name] = counts.get(name, 0) + 1
    text = README.read_text(encoding="utf-8")
    table = dict(re.findall(r"^\| `(test_\w+\.py)` \| (\d+) \|", text, flags=re.MULTILINE))
    assert {name: int(count) for name, count in table.items()} == counts
    assert f"**{sum(counts.values())} pruebas aprobadas, 0 fallidas, 0 omitidas**" in text

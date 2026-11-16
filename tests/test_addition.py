"""Máquina alteradora de suma binaria: resultados, acarreo, formato A#B, caché, IDs y cinta final.

La máquina se carga desde ``machines/transformer_binary_addition.yaml`` y la
ejecuta el motor genérico. El oráculo ``int(A, 2) + int(B, 2)`` solo existe en
estas pruebas: la máquina suma exclusivamente con sus reglas δ. Política de
salida: max(|A|, |B|) bits, uno más si hay desbordamiento, con los ceros
iniciales conservados.
"""

import random
from itertools import product
from pathlib import Path

import pytest

from src.input.machine_parser import parse_machine
from src.input.machine_validator import validate_machine
from src.input.yaml_loader import load_yaml
from src.model.simulation_result import Outcome
from src.model.transition import BLANK
from src.output.id_formatter import format_id
from src.output.tape_formatter import tape_contents
from src.simulator.engine import simulate
from src.simulator.trace import build_trace

ADDITION = Path(__file__).resolve().parents[1] / "machines" / "transformer_binary_addition.yaml"


@pytest.fixture(scope="module")
def loaded():
    machine, strings = parse_machine(load_yaml(ADDITION))
    validate_machine(machine, strings)
    return machine, strings


@pytest.fixture(scope="module")
def machine(loaded):
    return loaded[0]


def run(machine, word, **kwargs):
    return build_trace(simulate(machine, word, **kwargs))


def output(trace):
    return tape_contents(trace.final.tape)


def binary_sum(a, b):
    """Oráculo: valor de A + B con max(|A|, |B|) bits como mínimo."""
    return format(int(a, 2) + int(b, 2), f"0{max(len(a), len(b))}b")


def binary_words(lengths):
    return ["".join(bits) for n in lengths for bits in product("01", repeat=n)]


def check_sum(machine, a, b):
    trace = run(machine, f"{a}#{b}")
    result = output(trace)
    assert trace.outcome is Outcome.ACCEPTED, (a, b)
    assert (trace.final.state, trace.final.cache) == ("q9", BLANK), (a, b)
    assert result == binary_sum(a, b), (a, b)
    assert int(result, 2) == int(a, 2) + int(b, 2), (a, b)
    assert set(trace.final.tape.values()) <= {"0", "1"}, (a, b)
    # Región de salida contigua: termina donde terminaba A y crece hacia la izquierda.
    assert sorted(trace.final.tape) == list(range(len(a) - len(result), len(a))), (a, b)
    # Pasos (README.md, §13.7): T = |A#B| + m² + |B|² + 4m + 3, con m columnas procesadas.
    m = len(column_sums(a, b))
    assert trace.steps == len(a) + len(b) + 1 + m * m + len(b) ** 2 + 4 * m + 3, (a, b)
    return trace


def test_yaml_is_valid_and_declares_the_formal_components(loaded):
    machine, strings = loaded
    assert machine.states == {f"q{i}" for i in range(10)}
    assert (machine.input_alphabet, machine.tape_alphabet) == ({"0", "1", "#"}, {"0", "1", "#", "o", "i", BLANK})
    assert (machine.initial_state, machine.final_states) == ("q0", {"q9"})
    assert len(machine.transitions) == 57
    assert strings == ["1011#0110", "1111#0001", "10101#10111", "10000#00001"]


@pytest.mark.parametrize(
    ("word", "result", "steps", "final_id"),
    [
        ("1011#0110", "10001", 73, "[q9,B]10001BBBBB"),
        ("1111#0001", "10000", 73, "[q9,B]10000BBBBB"),
        ("10101#10111", "101100", 99, "[q9,B]101100BBBBBB"),
        ("10000#00001", "10001", 84, "[q9,B]10001BBBBBB"),
    ],
)
def test_demonstration_strings(machine, word, result, steps, final_id):
    trace = check_sum(machine, *word.split("#"))
    assert len(word) > 5
    assert (output(trace), trace.steps) == (result, steps)
    assert format_id(trace.final, len(word)) == final_id


def test_third_demonstration_is_21_plus_23():
    assert (int("10101", 2), int("10111", 2), int("101100", 2)) == (21, 23, 44)


@pytest.mark.parametrize(
    ("case", "a", "b", "result"),
    [
        ("A más corto que B", "1", "1011", "1100"),
        ("B más corto que A", "1011", "1", "1100"),
        ("acarreo en una sola columna", "01", "01", "10"),
        ("acarreo encadenado", "0111", "0001", "1000"),
        ("desbordamiento mínimo", "1", "1", "10"),
        ("desbordamiento con B más largo", "1", "111", "1000"),
        ("suma con cero a la derecha", "1010", "0", "1010"),
        ("suma con cero a la izquierda", "0", "1010", "1010"),
        ("cero más cero", "0", "0", "0"),
        ("ceros iniciales conservados", "0001", "0010", "0011"),
        ("ceros iniciales de ancho distinto", "00", "00001", "00001"),
        ("ambos operandos de unos", "1111", "1111", "11110"),
        ("sin acarreo", "1010", "0101", "1111"),
    ],
)
def test_complementary_cases(machine, case, a, b, result):
    assert output(check_sum(machine, a, b)) == result, case


@pytest.mark.parametrize(
    ("case", "word", "state"),
    [
        ("cadena vacía", "", "q0"),
        ("solo el separador", "#", "q0"),
        ("operando A vacío", "#01", "q0"),
        ("operando B vacío", "01#", "q2"),
        ("separador faltante", "1011", "q1"),
        ("separadores duplicados", "1#0#1", "q3"),
        ("separadores contiguos", "1##0", "q2"),
        ("separador al final", "10#01#", "q3"),
    ],
)
def test_malformed_strings_over_sigma_are_rejected_without_changing_the_tape(machine, case, word, state):
    """Cadenas de Σ* sin la forma A#B: la máquina se detiene sin regla, sin escribir nada."""
    trace = run(machine, word)
    assert (trace.outcome, trace.final.state) == (Outcome.REJECTED, state), case
    assert dict(trace.final.tape) == dict(enumerate(word)), case


@pytest.mark.parametrize("word", ["1a#0", "2#1", "1 0#1", "10+01", "o#i"])
def test_symbols_outside_sigma_are_an_input_error_not_a_rejection(machine, word):
    with pytest.raises(ValueError, match="fuera del alfabeto de entrada"):
        simulate(machine, word)


def test_every_pair_of_operands_up_to_length_4(machine):
    operands = binary_words(range(1, 5))
    for a in operands:
        for b in operands:
            check_sum(machine, a, b)


def test_random_longer_operands(machine):
    rng = random.Random(20261116)
    for _ in range(150):
        a, b = ("".join(rng.choice("01") for _ in range(rng.randint(1, 16))) for _ in range(2))
        check_sum(machine, a, b)


def column_sums(a, b):
    """Suma b_k + acarreo_k que debe viajar en la caché hacia cada columna k de A (oráculo)."""
    sums, carry = [], 0
    for k in range(max(len(a), len(b)) + 1):
        bit_b = int(b[-1 - k]) if k < len(b) else None
        if bit_b is None and carry == 0:
            break
        carried = (bit_b or 0) + carry
        sums.append(carried)
        bit_a = int(a[-1 - k]) if k < len(a) else 0
        carry = (bit_a + carried) // 2
    return sums


@pytest.mark.parametrize(("a", "b"), [("1011", "0110"), ("10101", "10111"), ("1", "111"), ("0111", "1"), ("0", "0")])
def test_cache_carries_each_column_sum_to_a(machine, a, b):
    """Al entrar a q6 la caché vale b_k + acarreo_k (blanco = 0); el estado no codifica ese valor."""
    entries = run(machine, f"{a}#{b}").entries
    carried = [
        0 if entry.cache is BLANK else int(entry.cache)
        for previous, entry in zip(entries, entries[1:])
        if entry.state == "q6" and previous.state != "q6"
    ]
    assert carried == column_sums(a, b)


def test_cache_domain_per_phase(machine):
    for entry in run(machine, "10101#10111").entries:
        if entry.state in {"q0", "q1", "q2", "q3", "q8", "q9"}:
            assert entry.cache is BLANK, entry.step
        elif entry.state in {"q4", "q7"}:
            assert entry.cache in {BLANK, "1"}, entry.step
        else:
            assert entry.cache in {BLANK, "1", "2"}, entry.step


def test_hand_trace_of_1_plus_1(machine):
    trace = run(machine, "1#1")
    assert [format_id(entry, 3) for entry in trace.entries] == [
        "[q0,B]1#1",
        "1[q1,B]#1",
        "1#[q2,B]1",
        "1#1[q3,B]B",
        "1#[q4,B]1",
        "1[q5,1]#B",
        "[q6,1]1#B",
        "o[q7,1]#B",
        "o#[q7,1]B",
        "o[q4,1]#B",
        "[q6,1]o#B",
        "[q6,1]Bo#B",
        "i[q7,B]o#B",
        "io[q7,B]#B",
        "io#[q7,B]B",
        "io[q4,B]#B",
        "i[q8,B]oBB",
        "[q8,B]i0BB",
        "[q8,B]B10BB",
        "[q9,B]10BB",
    ]


def test_step_limit_is_not_a_rejection(machine):
    trace = run(machine, "1011#0110", max_steps=40)
    assert (trace.outcome, trace.steps) == (Outcome.LIMIT_EXCEEDED, 40)
    assert run(machine, "1011#0110", max_steps=73).outcome is Outcome.ACCEPTED

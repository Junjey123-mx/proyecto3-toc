"""Máquina alteradora (incremento binario): salidas, desbordamiento, caché, IDs y pasos.

La máquina se carga desde ``machines/transformer_binary_increment.yaml`` y la
ejecuta el motor genérico. Los valores esperados vienen de la definición de f y
del análisis de ``docs/test_cases.md`` (sección 2). La salida es el contenido de
la cinta desde la primera hasta la última celda no blanca (``tape_contents``).
"""

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

TRANSFORMER = Path(__file__).resolve().parents[1] / "machines" / "transformer_binary_increment.yaml"


@pytest.fixture(scope="module")
def loaded():
    machine, strings = parse_machine(load_yaml(TRANSFORMER))
    validate_machine(machine, strings)
    return machine, strings


@pytest.fixture(scope="module")
def machine(loaded):
    return loaded[0]


def run(machine, word, **kwargs):
    return build_trace(simulate(machine, word, **kwargs))


def output(trace):
    return tape_contents(trace.final.tape)


def increment(word):
    """Definición de f: value₂(w) + 1 en binario, conservando los ceros a la izquierda."""
    return format(int(word, 2) + 1, f"0{len(word)}b")


def expected_steps(word):
    """T(w) = |w| + t + 2, con t = unos al final de w (docs/test_cases.md, §2.6)."""
    return len(word) + (len(word) - len(word.rstrip("1"))) + 2


def test_yaml_is_valid_and_declares_the_formal_components(loaded):
    machine, strings = loaded
    assert machine.states == {"q0", "q1", "q2"}
    assert (machine.input_alphabet, machine.tape_alphabet) == ({"0", "1"}, {"0", "1", BLANK})
    assert (machine.initial_state, machine.final_states) == ("q0", {"q2"})
    assert len(machine.transitions) == 6
    assert strings == ["10101", "11011", "11111", "10000"]


@pytest.mark.parametrize(
    ("word", "result", "steps", "final_id"),
    [
        ("10101", "10110", 8, "101[q2,B]10"),
        ("11011", "11100", 9, "11[q2,B]100"),
        ("11111", "100000", 12, "[q2,B]100000"),
        ("10000", "10001", 7, "1000[q2,B]1"),
    ],
)
def test_demonstration_strings(machine, word, result, steps, final_id):
    trace = run(machine, word)
    assert len(word) >= 5
    assert (trace.outcome, trace.final.state, trace.final.cache) == (Outcome.ACCEPTED, "q2", BLANK)
    assert (output(trace), trace.steps) == (result, steps)
    assert format_id(trace.final, len(word)) == final_id


@pytest.mark.parametrize(
    ("word", "result"),
    [("0", "1"), ("1", "10"), ("111", "1000"), ("1010", "1011"), ("0011", "0100"), ("0111", "1000"), ("01", "10")],
)
def test_complementary_cases(machine, word, result):
    trace = run(machine, word)
    assert (trace.outcome, output(trace)) == (Outcome.ACCEPTED, result)
    assert trace.steps == expected_steps(word)


def test_overflow_writes_the_new_bit_at_a_negative_position(machine):
    final = run(machine, "11111").final
    assert (final.head, min(final.tape), max(final.tape)) == (-1, -1, 4)
    assert dict(final.tape) == {-1: "1", 0: "0", 1: "0", 2: "0", 3: "0", 4: "0"}


def test_hand_trace_of_11111(machine):
    """docs/test_cases.md, §2.7, con el número de regla aplicada."""
    trace = run(machine, "11111")
    expected = [
        ("[q0,B]11111", None), ("1[q0,B]1111", 2), ("11[q0,B]111", 2), ("111[q0,B]11", 2),
        ("1111[q0,B]1", 2), ("11111[q0,B]B", 2), ("1111[q1,1]1", 3), ("111[q1,1]10", 4),
        ("11[q1,1]100", 4), ("1[q1,1]1000", 4), ("[q1,1]10000", 4), ("[q1,1]B00000", 4),
        ("[q2,B]100000", 6),
    ]
    rules = machine.transitions
    observed = [
        (format_id(e, 5), None if e.applied is None else rules.index(e.applied) + 1) for e in trace.entries
    ]
    assert observed == expected


def test_hand_trace_of_10101(machine):
    """docs/test_cases.md, §2.8."""
    assert [format_id(e, 5) for e in run(machine, "10101").entries] == [
        "[q0,B]10101", "1[q0,B]0101", "10[q0,B]101", "101[q0,B]01", "1010[q0,B]1",
        "10101[q0,B]B", "1010[q1,1]1", "101[q1,1]00", "101[q2,B]10",
    ]


def test_cache_holds_the_carry_only_while_it_propagates(machine):
    for entry in run(machine, "10111").entries:
        assert entry.cache == ("1" if entry.state == "q1" else BLANK)


@pytest.mark.parametrize("word", ["1" * 60, "1" + "0" * 59, "10" * 30, "0" * 40 + "1" * 20])
def test_long_inputs(machine, word):
    trace = run(machine, word)
    assert (trace.outcome, output(trace), trace.steps) == (Outcome.ACCEPTED, increment(word), expected_steps(word))


def test_every_binary_string_up_to_length_10_is_incremented(machine):
    for length in range(1, 11):
        for bits in product("01", repeat=length):
            word = "".join(bits)
            trace = run(machine, word)
            assert (trace.outcome, output(trace)) == (Outcome.ACCEPTED, increment(word)), word
            assert trace.steps == expected_steps(word), word


def test_output_is_never_erased_and_has_no_blanks(machine):
    for word in ["0", "1", "10101", "11111", "00000"]:
        result = output(run(machine, word))
        assert len(result) in (len(word), len(word) + 1)
        assert set(result) <= {"0", "1"}


def test_empty_input_is_treated_as_zero(machine):
    trace = run(machine, "")
    assert (trace.outcome, output(trace), trace.steps) == (Outcome.ACCEPTED, "1", 2)


def test_step_limit_is_not_a_rejection(machine):
    short = run(machine, "11111", max_steps=11)
    exact = run(machine, "11111", max_steps=12)
    assert (short.outcome, short.steps) == (Outcome.LIMIT_EXCEEDED, 11)
    assert (exact.outcome, output(exact)) == (Outcome.ACCEPTED, "100000")


def test_strings_are_simulated_independently(machine):
    first = run(machine, "11111")
    run(machine, "10000")
    again = run(machine, "11111")
    assert again == first and output(again) == "100000"

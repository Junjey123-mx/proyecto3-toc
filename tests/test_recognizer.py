"""Máquina reconocedora L = {aⁿbⁿ | n ≥ 1}: demostración, bordes, IDs y límite de pasos.

La máquina se carga desde ``machines/recognizer_anbn.yaml`` y la ejecuta el
motor genérico; los valores esperados provienen del análisis de
``README.md`` (sección 10), no de otra implementación del lenguaje.
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
from src.simulator.engine import simulate
from src.simulator.trace import build_trace

RECOGNIZER = Path(__file__).resolve().parents[1] / "machines" / "recognizer_anbn.yaml"


@pytest.fixture(scope="module")
def loaded():
    machine, strings = parse_machine(load_yaml(RECOGNIZER))
    validate_machine(machine, strings)
    return machine, strings


@pytest.fixture(scope="module")
def machine(loaded):
    return loaded[0]


def run(machine, word, **kwargs):
    return build_trace(simulate(machine, word, **kwargs))


def accepted_steps(n):
    """T(n) = 2n² + 2n + 1 (README.md, §10.5)."""
    return 2 * n * n + 2 * n + 1


def in_language(word):
    """Definición de L: n letras a seguidas de n letras b, con n ≥ 1."""
    n = len(word) // 2
    return n >= 1 and word == "a" * n + "b" * n


def test_yaml_is_valid_and_declares_the_formal_components(loaded):
    machine, strings = loaded
    assert machine.states == {"q0", "q1", "q2", "q3", "q4"}
    assert (machine.input_alphabet, machine.tape_alphabet) == ({"a", "b"}, {"a", "b", "X", "Y", BLANK})
    assert (machine.initial_state, machine.final_states) == ("q0", {"q4"})
    assert len(machine.transitions) == 10
    assert strings == ["aaabbb", "aaaabbbb", "aaabb", "aabbbb"]


def test_cache_is_blank_in_every_rule(machine):
    assert all(rule.cache is BLANK and rule.next_cache is BLANK for rule in machine.transitions)


@pytest.mark.parametrize(
    ("word", "outcome", "steps", "state", "final_id"),
    [
        ("aaabbb", Outcome.ACCEPTED, 25, "q4", "XXXYYYB[q4,B]B"),
        ("aaaabbbb", Outcome.ACCEPTED, 41, "q4", "XXXXYYYYB[q4,B]B"),
        ("aaabb", Outcome.REJECTED, 17, "q1", "XXXYY[q1,B]B"),
        ("aabbbb", Outcome.REJECTED, 12, "q3", "XXYY[q3,B]bb"),
    ],
)
def test_demonstration_strings(machine, word, outcome, steps, state, final_id):
    trace = run(machine, word)
    assert len(word) >= 5
    assert (trace.outcome, trace.steps, trace.final.state) == (outcome, steps, state)
    assert format_id(trace.final, len(word)) == final_id
    assert len(trace.entries) == steps + 1


@pytest.mark.parametrize(
    ("word", "reason"),
    [
        ("aaabb", "no hay regla para el estado 'q1' con caché el blanco leyendo el blanco, y 'q1' no es final"),
        ("aabbbb", "no hay regla para el estado 'q3' con caché el blanco leyendo 'b', y 'q3' no es final"),
    ],
)
def test_rejections_are_justified_by_a_missing_rule(machine, word, reason):
    trace = run(machine, word)
    final = trace.final
    assert machine.find_transition(final.state, final.cache, final.scanned) is None
    assert final.state not in machine.final_states
    assert trace.reason == reason


def test_hand_trace_of_aabb(machine):
    """Recorrido a mano de README.md, §10.6, con la regla aplicada en cada paso."""
    trace = run(machine, "aabb")
    expected = [
        ("[q0,B]aabb", None), ("X[q1,B]abb", 1), ("Xa[q1,B]bb", 3), ("X[q2,B]aYb", 5),
        ("[q2,B]XaYb", 6), ("X[q0,B]aYb", 8), ("XX[q1,B]Yb", 1), ("XXY[q1,B]b", 4),
        ("XX[q2,B]YY", 5), ("X[q2,B]XYY", 7), ("XX[q0,B]YY", 8), ("XXY[q3,B]Y", 2),
        ("XXYY[q3,B]B", 9), ("XXYYB[q4,B]B", 10),
    ]
    rules = machine.transitions
    observed = [
        (format_id(e, 4), None if e.applied is None else rules.index(e.applied) + 1) for e in trace.entries
    ]
    assert observed == expected
    assert trace.outcome is Outcome.ACCEPTED


def test_hand_trace_of_abb(machine):
    trace = run(machine, "abb")
    assert [format_id(e, 3) for e in trace.entries] == [
        "[q0,B]abb", "X[q1,B]bb", "[q2,B]XYb", "X[q0,B]Yb", "XY[q3,B]b",
    ]
    assert trace.outcome is Outcome.REJECTED


@pytest.mark.parametrize(
    ("word", "outcome", "state", "scanned"),
    [
        ("ab", Outcome.ACCEPTED, "q4", BLANK),
        ("aabb", Outcome.ACCEPTED, "q4", BLANK),
        ("abb", Outcome.REJECTED, "q3", "b"),
        ("aab", Outcome.REJECTED, "q1", BLANK),
        ("ba", Outcome.REJECTED, "q0", "b"),
        ("abab", Outcome.REJECTED, "q3", "a"),
        ("aaaa", Outcome.REJECTED, "q1", BLANK),
        ("bbbb", Outcome.REJECTED, "q0", "b"),
        ("", Outcome.REJECTED, "q0", BLANK),
        ("aabba", Outcome.REJECTED, "q3", "a"),
        ("abba", Outcome.REJECTED, "q3", "b"),
    ],
)
def test_complementary_cases(machine, word, outcome, state, scanned):
    trace = run(machine, word)
    assert (trace.outcome, trace.final.state, trace.final.scanned) == (outcome, state, scanned)


def test_empty_input_is_rejected_without_transitions(machine):
    trace = run(machine, "")
    assert (trace.outcome, trace.steps, format_id(trace.final, 0)) == (Outcome.REJECTED, 0, "[q0,B]B")


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 10, 25])
def test_accepted_step_count_follows_the_formula(machine, n):
    trace = run(machine, "a" * n + "b" * n)
    assert (trace.outcome, trace.steps) == (Outcome.ACCEPTED, accepted_steps(n))
    assert format_id(trace.final, 2 * n) == "X" * n + "Y" * n + "B[q4,B]B"


@pytest.mark.parametrize(("a", "b"), [(10, 9), (9, 10), (25, 24), (1, 0), (0, 1)])
def test_long_unbalanced_strings_are_rejected(machine, a, b):
    assert run(machine, "a" * a + "b" * b).outcome is Outcome.REJECTED


def test_every_string_up_to_length_10_matches_the_definition_of_l(machine):
    for length in range(11):
        for letters in product("ab", repeat=length):
            word = "".join(letters)
            outcome = run(machine, word).outcome
            assert outcome is (Outcome.ACCEPTED if in_language(word) else Outcome.REJECTED), word


def test_step_limit_is_not_a_rejection(machine):
    short = run(machine, "aaaabbbb", max_steps=40)
    exact = run(machine, "aaaabbbb", max_steps=41)
    assert (short.outcome, short.steps) == (Outcome.LIMIT_EXCEEDED, 40)
    assert (exact.outcome, exact.steps) == (Outcome.ACCEPTED, 41)


def test_strings_are_simulated_independently(machine):
    first = run(machine, "aaabbb")
    run(machine, "aaabb")
    assert run(machine, "aaabbb") == first

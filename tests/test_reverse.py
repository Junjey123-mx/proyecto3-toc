"""Máquina alteradora de inversión: salidas, invariante de rondas, caché, IDs y pasos.

La máquina se carga desde ``machines/transformer_binary_reverse.yaml`` y la
ejecuta el motor genérico. El oráculo es ``w[::-1]``, que solo se usa aquí: la
máquina invierte la cadena exclusivamente con sus reglas δ. La salida es el
contenido de la cinta desde la primera hasta la última celda no blanca.
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

REVERSE = Path(__file__).resolve().parents[1] / "machines" / "transformer_binary_reverse.yaml"
PLACED = {"0": "o", "1": "i"}
"""Marca de un bit que ya está en su posición final."""


@pytest.fixture(scope="module")
def loaded():
    machine, strings = parse_machine(load_yaml(REVERSE))
    validate_machine(machine, strings)
    return machine, strings


@pytest.fixture(scope="module")
def machine(loaded):
    return loaded[0]


def run(machine, word, **kwargs):
    return build_trace(simulate(machine, word, **kwargs))


def output(trace):
    return tape_contents(trace.final.tape)


def expected_steps(word):
    """T(0) = 1 y T(n) = ⌊(n² + 6n + 6) / 2⌋ para n ≥ 1."""
    n = len(word)
    return 1 if n == 0 else (n * n + 6 * n + 6) // 2


def binary_words(lengths):
    return ["".join(bits) for n in lengths for bits in product("01", repeat=n)]


def test_yaml_is_valid_and_declares_the_formal_components(loaded):
    machine, strings = loaded
    assert machine.states == {f"q{i}" for i in range(7)}
    assert (machine.input_alphabet, machine.tape_alphabet) == ({"0", "1"}, {"0", "1", "o", "i", "*", BLANK})
    assert (machine.initial_state, machine.final_states) == ("q0", {"q6"})
    assert len(machine.transitions) == 33
    assert strings == ["10110", "11001", "10000", "11100"]


@pytest.mark.parametrize(
    ("word", "result", "final_id"),
    [
        ("10110", "01101", "01101[q6,B]B"),
        ("11001", "10011", "10011[q6,B]B"),
        ("10000", "00001", "00001[q6,B]B"),
        ("11100", "00111", "00111[q6,B]B"),
    ],
)
def test_demonstration_strings(machine, word, result, final_id):
    trace = run(machine, word)
    assert len(word) >= 5
    assert (trace.outcome, trace.final.state, trace.final.cache) == (Outcome.ACCEPTED, "q6", BLANK)
    assert (output(trace), trace.steps) == (result, 30)
    assert format_id(trace.final, len(word)) == final_id


@pytest.mark.parametrize(
    ("case", "word"),
    [
        ("palíndromo impar", "10101"),
        ("palíndromo par", "0110"),
        ("palíndromo largo", "1001001"),
        ("todos ceros", "00000"),
        ("todos unos", "1111111"),
        ("alternancia par", "010101"),
        ("alternancia impar", "1010101"),
        ("ceros iniciales", "00011"),
        ("ceros finales", "11000"),
        ("un bit", "0"),
        ("dos bits", "10"),
        ("longitud par", "11010010"),
        ("longitud impar", "110100101"),
    ],
)
def test_complementary_cases(machine, case, word):
    trace = run(machine, word)
    assert trace.outcome is Outcome.ACCEPTED, case
    assert output(trace) == word[::-1]
    assert trace.steps == expected_steps(word)


def test_empty_input_is_its_own_reverse(machine):
    trace = run(machine, "")
    assert (trace.outcome, trace.steps, dict(trace.final.tape)) == (Outcome.ACCEPTED, 1, {})


def test_hand_trace_of_10110(machine):
    """Fin de cada ronda: el par colocado se lee en las marcas o/i (README.md, §12.7)."""
    trace = run(machine, "10110")
    ids = {entry.step: format_id(entry, 5) for entry in trace.entries}
    assert ids[0] == "[q0,B]10110"
    assert ids[1] == "*[q1,1]0110"
    assert ids[7] == "*01[q3,0]1i"
    assert ids[11] == "o[q0,B]011i"
    assert ids[18] == "oi[q0,B]1oi"
    assert ids[21] == "o[q4,B]iioi"
    assert ids[24] == "[q5,B]oiioi"
    assert ids[30] == "01101[q6,B]B"


def test_every_binary_string_up_to_length_10_is_reversed(machine):
    for word in binary_words(range(11)):
        trace = run(machine, word)
        assert trace.outcome is Outcome.ACCEPTED, word
        assert (trace.final.state, trace.final.cache) == ("q6", BLANK), word
        assert output(trace) == word[::-1], word
        assert trace.steps == expected_steps(word), word
        assert sorted(trace.final.tape) == list(range(len(word))), word
        assert set(trace.final.tape.values()) <= {"0", "1"}, word


def test_each_round_places_one_pair_of_mirror_bits(machine):
    """Invariante: al volver a q0 por j-ésima vez, los j bits de cada extremo ya están invertidos y marcados."""
    for word in binary_words(range(1, 8)):
        n = len(word)
        visits = [entry for entry in run(machine, word).entries if entry.state == "q0"]
        for j, entry in enumerate(visits):
            for k in range(min(j, n)):
                assert entry.tape.get(k) == PLACED[word[n - 1 - k]], (word, j, k)
                assert entry.tape.get(n - 1 - k) == PLACED[word[k]], (word, j, k)
            assert [entry.tape.get(k) for k in range(j, n - j)] == list(word[j:n - j]), (word, j)
        assert len(visits) == (n + 1) // 2 + (n % 2 == 0), word


def test_cache_carries_the_bit_taken_from_the_hole(machine):
    """La caché guarda el bit en tránsito; el estado solo indica la fase, no el valor."""
    for word in ["10110", "0110", "1001110"]:
        for entry in run(machine, word).entries:
            if entry.state == "q1":
                hole = next(k for k, symbol in entry.tape.items() if symbol == "*")
                assert entry.cache == word[hole], (word, entry.step)
            elif entry.state in {"q0", "q4", "q5", "q6"}:
                assert entry.cache is BLANK, (word, entry.step)
            else:
                assert entry.cache in {"0", "1"}, (word, entry.step)


@pytest.mark.parametrize("word", ["1" * 40, "0" * 39 + "1", "10" * 20, "1101" * 9 + "0"])
def test_long_inputs(machine, word):
    trace = run(machine, word)
    assert (trace.outcome, output(trace), trace.steps) == (Outcome.ACCEPTED, word[::-1], expected_steps(word))


def test_symbols_outside_sigma_are_an_input_error_not_a_rejection(machine):
    with pytest.raises(ValueError, match="fuera del alfabeto de entrada"):
        simulate(machine, "10o1")


def test_step_limit_is_not_a_rejection(machine):
    trace = run(machine, "10110", max_steps=10)
    assert (trace.outcome, trace.steps) == (Outcome.LIMIT_EXCEEDED, 10)
    assert run(machine, "10110", max_steps=30).outcome is Outcome.ACCEPTED

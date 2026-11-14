"""Interpretación del esquema YAML del curso: estructura, tipos, blanco, caché y movimientos."""

from pathlib import Path

import pytest

from src.input.errors import InputError, MachineParseError
from src.input.machine_parser import parse_machine
from src.input.yaml_loader import load_yaml
from src.model.transition import BLANK, Move, Transition

ROOT = Path(__file__).resolve().parents[1]
STATEMENT_EXAMPLE = ROOT / "tests" / "fixtures" / "statement_example_mt_1.yaml"
LAB10_MACHINE = ROOT / "machines" / "examples" / "basic_machine.yaml"


def minimal_document():
    return {
        "q_states": {"q_list": ["q0", "q1"], "initial": "q0", "final": "q1"},
        "alphabet": ["a"],
        "tape_alphabet": ["a", None],
        "delta": [
            {
                "params": {"initial_state": "q0", "mem_cache_value": None, "tape_input": "a"},
                "output": {
                    "final_state": "q1",
                    "mem_cache_value": "a",
                    "tape_output": None,
                    "tape_displacement": "R",
                },
            }
        ],
        "simulation_strings": ["a", "", "aa"],
    }


def parse_error(document):
    with pytest.raises(MachineParseError) as error:
        parse_machine(document)
    return str(error.value)


def test_minimal_document_maps_every_field():
    machine, strings = parse_machine(minimal_document())

    assert machine.states == {"q0", "q1"}
    assert machine.initial_state == "q0"
    assert machine.final_states == {"q1"}
    assert machine.input_alphabet == {"a"}
    assert machine.tape_alphabet == {"a", BLANK}
    assert machine.transitions == (Transition("q0", BLANK, "a", "q1", "a", BLANK, Move.R),)
    assert strings == ["a", "", "aa"]


def test_statement_example_is_parsed_without_altering_its_data():
    machine, strings = parse_machine(load_yaml(STATEMENT_EXAMPLE))

    assert machine.states == {"0", "1", "2", "3", "4", "5"}
    assert (machine.initial_state, machine.final_states) == ("0", {"5"})
    assert machine.input_alphabet == {"a", "b"}
    assert machine.tape_alphabet == {"#", "X", BLANK}
    assert machine.transitions == (
        Transition("0", BLANK, "a", "1", "a", BLANK, Move.R),
        Transition("0", BLANK, "b", "1", "a", BLANK, Move.R),
    )
    assert strings == ["aab#aab", "ab#ab", "abbababa#aba"]


def lab10_rules():
    """δ del Laboratorio 10 con w ∈ {a, b} expandido, escrito a partir del enunciado del lab."""
    rules = {
        ("0", BLANK, "#", "4", BLANK, "#", Move.R),
        ("3", BLANK, BLANK, "0", BLANK, BLANK, Move.R),
        ("4", BLANK, "X", "4", BLANK, "X", Move.R),
        ("4", BLANK, BLANK, "5", BLANK, BLANK, Move.R),
    }
    for w in "ab":
        rules |= {
            ("0", BLANK, w, "1", w, BLANK, Move.R),
            ("1", w, "a", "1", w, "a", Move.R),
            ("1", w, "b", "1", w, "b", Move.R),
            ("1", w, "#", "2", w, "#", Move.R),
            ("2", w, "X", "2", w, "X", Move.R),
            ("2", w, w, "3", BLANK, "X", Move.L),
        }
    rules |= {("3", BLANK, s, "3", BLANK, s, Move.L) for s in "X#ab"}
    return {Transition(*rule) for rule in rules}


def test_lab10_fixture_matches_the_lab_transition_table():
    machine, strings = parse_machine(load_yaml(LAB10_MACHINE))

    assert len(machine.transitions) == 20
    assert set(machine.transitions) == lab10_rules()
    assert machine.input_alphabet == {"a", "b", "#"}
    assert machine.tape_alphabet == {"a", "b", "#", "X", BLANK}
    assert strings == ["aab#aab", "ab#ab", "abbababa#aba", "abb#aab", "#"]


@pytest.mark.parametrize(
    ("path", "message"),
    [
        (("q_states",), "raíz: falta la clave obligatoria 'q_states'"),
        (("q_states", "q_list"), "q_states: falta la clave obligatoria 'q_list'"),
        (("q_states", "initial"), "q_states: falta la clave obligatoria 'initial'"),
        (("q_states", "final"), "q_states: falta la clave obligatoria 'final'"),
        (("alphabet",), "raíz: falta la clave obligatoria 'alphabet'"),
        (("tape_alphabet",), "raíz: falta la clave obligatoria 'tape_alphabet'"),
        (("delta",), "raíz: falta la clave obligatoria 'delta'"),
        (("simulation_strings",), "raíz: falta la clave obligatoria 'simulation_strings'"),
        (("delta", 0, "output"), "delta[0]: falta la clave obligatoria 'output'"),
        (("delta", 0, "params", "mem_cache_value"), "delta[0].params: falta la clave obligatoria 'mem_cache_value'"),
        (("delta", 0, "output", "tape_output"), "delta[0].output: falta la clave obligatoria 'tape_output'"),
        (("delta", 0, "output", "tape_displacement"), "delta[0].output: falta la clave obligatoria 'tape_displacement'"),
    ],
)
def test_missing_required_key_is_reported_with_its_path(path, message):
    document = minimal_document()
    container = document
    for step in path[:-1]:
        container = container[step]
    del container[path[-1]]
    assert parse_error(document) == message


def test_present_but_empty_cache_value_means_blank():
    machine, _ = parse_machine(minimal_document())
    assert machine.transitions[0].cache is BLANK


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda d: d["q_states"].update(q_list=[0, 1]), "q_states.q_list[0]: se esperaba una cadena no vacía, no 0; en YAML escríbalo entre comillas"),
        (lambda d: d["q_states"].update(initial=0), "q_states.initial: se esperaba una cadena no vacía, no 0; en YAML"),
        (lambda d: d.update(alphabet=[True]), "alphabet[0]: se esperaba una cadena no vacía, no True; en YAML"),
        (lambda d: d["q_states"].update(q_list=["q0", None]), "q_states.q_list[1]: el blanco (entrada vacía) no está permitido aquí"),
        (lambda d: d.update(alphabet=["a", None]), "alphabet[1]: el blanco (entrada vacía) no está permitido aquí"),
        (lambda d: d["delta"][0]["params"].update(initial_state=None), "delta[0].params.initial_state: el blanco (entrada vacía) no está permitido aquí"),
        (lambda d: d["delta"][0]["params"].update(tape_input=""), "delta[0].params.tape_input: se esperaba una cadena no vacía, no ''"),
        (lambda d: d["delta"][0]["output"].update(mem_cache_value=["a"]), "delta[0].output.mem_cache_value: se esperaba una cadena no vacía, no ['a']"),
        (lambda d: d.update(simulation_strings=[None]), "simulation_strings[0]: se esperaba una cadena, no None; la cadena vacía se escribe ''"),
        (lambda d: d.update(simulation_strings=[10101]), "simulation_strings[0]: se esperaba una cadena, no 10101; en YAML"),
        (lambda d: d.update(delta=None), "delta: se esperaba una lista, no None"),
        (lambda d: d["delta"][0].update(params=["q0"]), "delta[0].params: se esperaba un mapeo, no ['q0']"),
        (lambda d: d.update(q_states="q0"), "q_states: se esperaba un mapeo, no 'q0'"),
    ],
)
def test_wrong_types_are_rejected_with_path_and_hint(change, message):
    document = minimal_document()
    change(document)
    assert parse_error(document).startswith(message)


@pytest.mark.parametrize("move", ["D", "l", "r", "LEFT", None, 1])
def test_only_l_r_s_moves_are_accepted(move):
    document = minimal_document()
    document["delta"][0]["output"]["tape_displacement"] = move
    assert "delta[0].output.tape_displacement: debe ser L, R o S" in parse_error(document)


@pytest.mark.parametrize(("move", "expected"), [("L", Move.L), ("R", Move.R), ("S", Move.S)])
def test_moves_map_to_enum(move, expected):
    document = minimal_document()
    document["delta"][0]["output"]["tape_displacement"] = move
    assert parse_machine(document)[0].transitions[0].move is expected


def test_letter_b_is_an_ordinary_symbol_not_the_blank():
    document = minimal_document()
    document["tape_alphabet"] = ["a", "B", None]
    machine, _ = parse_machine(document)
    assert machine.tape_alphabet == {"a", "B", BLANK}


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda d: d["q_states"].update(q_list=["q0", "q0", "q1"]), "q_states.q_list: elementos repetidos: 'q0'"),
        (lambda d: d.update(tape_alphabet=[None, "a", None]), "tape_alphabet: elementos repetidos: None"),
        (lambda d: d.update(alphabet=["a", "a"]), "alphabet: elementos repetidos: 'a'"),
    ],
)
def test_repeated_entries_are_rejected(change, message):
    document = minimal_document()
    change(document)
    assert parse_error(document) == message


def test_final_may_be_a_list_of_states():
    document = minimal_document()
    document["q_states"]["final"] = ["q0", "q1"]
    assert parse_machine(document)[0].final_states == {"q0", "q1"}


def test_duplicate_delta_keys_are_reported_with_positions():
    document = minimal_document()
    document["delta"].append(document["delta"][0])
    assert parse_error(document).startswith("delta: δ no es determinista: las reglas 0 y 1 están duplicadas")


def test_root_must_be_a_mapping():
    assert parse_error(["q_states"]) == "raíz: se esperaba un mapeo, no ['q_states']"


def test_parse_errors_are_input_errors():
    assert issubclass(MachineParseError, InputError)

"""Validación formal: matriz de máquinas válidas e inválidas y errores localizados."""

from pathlib import Path

import pytest

from src.input.errors import InputError, MachineValidationError
from src.input.machine_parser import parse_machine
from src.input.machine_validator import validate_machine
from src.input.yaml_loader import load_yaml
from src.model.transition import BLANK, Move, Transition
from src.model.turing_machine import TuringMachine

ROOT = Path(__file__).resolve().parents[1]
RULE = Transition("q0", BLANK, "a", "q1", "a", "X", Move.R)


def build(**changes):
    fields = {
        "states": {"q0", "q1"},
        "input_alphabet": {"a"},
        "tape_alphabet": {"a", "X", BLANK},
        "initial_state": "q0",
        "final_states": {"q1"},
        "transitions": (RULE,),
    }
    fields.update(changes)
    return TuringMachine(**fields)


def errors_of(machine, strings=()):
    with pytest.raises(MachineValidationError) as error:
        validate_machine(machine, list(strings))
    return error.value.errors


def test_lab10_reference_machine_is_valid():
    machine, strings = parse_machine(load_yaml(ROOT / "machines" / "examples" / "basic_machine.yaml"))
    snapshot = (machine.states, machine.tape_alphabet, machine.transitions)
    validate_machine(machine, strings)
    assert (machine.states, machine.tape_alphabet, machine.transitions) == snapshot


def test_minimal_machine_and_empty_input_are_valid():
    validate_machine(build(), ["", "a", "aaaa"])


def test_statement_example_reports_each_inconsistency_of_the_printed_yaml():
    machine, strings = parse_machine(load_yaml(ROOT / "tests" / "fixtures" / "statement_example_mt_1.yaml"))
    assert errors_of(machine, strings) == [
        "tape_alphabet: debe incluir los símbolos de alphabet; faltan ['a', 'b']",
        "delta[0].params.tape_input: 'a' no pertenece a tape_alphabet",
        "delta[1].params.tape_input: 'b' no pertenece a tape_alphabet",
        "simulation_strings[0]: 'aab#aab' usa símbolos fuera de alphabet: ['#']",
        "simulation_strings[1]: 'ab#ab' usa símbolos fuera de alphabet: ['#']",
        "simulation_strings[2]: 'abbababa#aba' usa símbolos fuera de alphabet: ['#']",
    ]


@pytest.mark.parametrize(
    ("machine", "message"),
    [
        (build(states=set(), initial_state="q0", final_states=set(), transitions=()), "q_states.q_list: debe declarar al menos un estado"),
        (build(initial_state="q9"), "q_states.initial: 'q9' no pertenece a q_list"),
        (build(final_states=set()), "q_states.final: debe declarar al menos un estado final"),
        (build(final_states={"q1", "q7"}), "q_states.final: 'q7' no pertenece a q_list"),
        (build(input_alphabet=set(), transitions=()), "alphabet: debe declarar al menos un símbolo de entrada"),
        (build(input_alphabet={"a", BLANK}), "alphabet: el blanco no puede ser un símbolo de entrada"),
        (build(tape_alphabet={"a", "X"}), "tape_alphabet: debe incluir el blanco como entrada vacía ('-')"),
        (build(input_alphabet={"a", "b"}), "tape_alphabet: debe incluir los símbolos de alphabet; faltan ['b']"),
        (build(input_alphabet={"a", "ab"}, tape_alphabet={"a", "ab", "X", BLANK}), "alphabet: 'ab' debe ser un único carácter"),
        (build(tape_alphabet={"a", "X1", BLANK}), "tape_alphabet: 'X1' debe ser un único carácter"),
        (build(transitions=(Transition("q5", BLANK, "a", "q1", "a", "a", Move.R),)), "delta[0].params.initial_state: 'q5' no pertenece a q_list"),
        (build(transitions=(Transition("q0", BLANK, "c", "q1", "a", "a", Move.R),)), "delta[0].params.tape_input: 'c' no pertenece a tape_alphabet"),
        (build(transitions=(Transition("q0", BLANK, "a", "q8", "a", "a", Move.R),)), "delta[0].output.final_state: 'q8' no pertenece a q_list"),
        (build(transitions=(Transition("q0", BLANK, "a", "q1", "a", "Y", Move.R),)), "delta[0].output.tape_output: 'Y' no pertenece a tape_alphabet"),
        (build(tape_alphabet={"a", "X"}, transitions=(Transition("q0", BLANK, BLANK, "q1", BLANK, "a", Move.S),)), "delta[0].params.tape_input: el blanco no pertenece a tape_alphabet"),
    ],
)
def test_invalid_definitions_are_reported_with_their_field(machine, message):
    assert any(error.startswith(message) for error in errors_of(machine)), errors_of(machine)


@pytest.mark.parametrize("word", ["X", "aXa", "ab"])
def test_strings_must_use_only_input_symbols_even_if_they_are_tape_symbols(word):
    assert errors_of(build(), [word])[0].startswith("simulation_strings[0]:")


def test_cache_values_are_not_restricted_to_the_tape_alphabet():
    remember = Transition("q0", BLANK, "a", "q1", "memoria", "a", Move.R)
    validate_machine(build(transitions=(remember,)), ["a"])


def test_rules_leaving_a_final_state_are_accepted():
    loop = Transition("q1", BLANK, "a", "q1", BLANK, "a", Move.R)
    validate_machine(build(transitions=(RULE, loop)), ["a"])


def test_all_problems_are_collected_in_a_single_error():
    machine = build(initial_state="q9", final_states={"q7"}, tape_alphabet={"a", "X"})
    with pytest.raises(MachineValidationError) as error:
        validate_machine(machine, ["b"])

    assert len(error.value.errors) == 4
    assert str(error.value).startswith("la máquina no es válida:\n- q_states.initial: 'q9'")
    assert all(f"- {line}" in str(error.value) for line in error.value.errors)


def test_validation_errors_are_input_errors():
    assert issubclass(MachineValidationError, InputError)

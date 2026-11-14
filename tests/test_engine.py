"""Motor: ID_0, aceptación, rechazo, límite de pasos, independencia y trazas de los laboratorios."""

from pathlib import Path

import pytest

from src.input.machine_parser import parse_machine
from src.input.machine_validator import validate_machine
from src.input.yaml_loader import load_yaml
from src.model.simulation_result import Outcome
from src.model.transition import BLANK, Move, Transition
from src.model.turing_machine import TuringMachine
from src.simulator.engine import DEFAULT_MAX_STEPS, simulate
from src.simulator.step import step

LAB10 = Path(__file__).resolve().parents[1] / "machines" / "examples" / "basic_machine.yaml"


def lab10():
    machine, strings = parse_machine(load_yaml(LAB10))
    validate_machine(machine, strings)
    return machine


def rule(state, read, next_state, write, move, cache=BLANK, next_cache=BLANK):
    return {
        "params": {"initial_state": state, "mem_cache_value": cache, "tape_input": read},
        "output": {
            "final_state": next_state,
            "mem_cache_value": next_cache,
            "tape_output": write,
            "tape_displacement": move,
        },
    }


def lab9_incrementer():
    """Laboratorio 9, ejercicio 2: suma 1 en binario conservando la longitud (sin caché)."""
    document = {
        "q_states": {"q_list": ["q0", "q1", "qhalt"], "initial": "q0", "final": "qhalt"},
        "alphabet": ["0", "1"],
        "tape_alphabet": ["0", "1", None],
        "delta": [
            rule("q0", "0", "q0", "0", "R"),
            rule("q0", "1", "q0", "1", "R"),
            rule("q0", None, "q1", None, "L"),
            rule("q1", "0", "qhalt", "1", "R"),
            rule("q1", "1", "q1", "0", "L"),
            rule("q1", None, "qhalt", None, "L"),
        ],
        "simulation_strings": ["100", "10011", "11"],
    }
    machine, strings = parse_machine(document)
    validate_machine(machine, strings)
    return machine


def tiny(*rules, final="f"):
    return TuringMachine({"s", "t", "f"}, {"a"}, {"a", "X", BLANK}, "s", final, rules)


def test_initial_configuration_follows_the_lab10_notation():
    first = simulate(lab10(), "aab#aab").configurations[0]
    assert (first.step_index, first.state, first.cache, first.head, first.applied) == (0, "0", BLANK, 0, None)
    assert dict(first.tape) == dict(enumerate("aab#aab"))


@pytest.mark.parametrize(
    ("word", "outcome", "steps", "state", "cache", "head", "tape"),
    [
        # Lab 10 b): [q0,B]aab#aab ⊢^32 BBB#XXXB[q5,B]B
        ("aab#aab", Outcome.ACCEPTED, 32, "5", BLANK, 8, {3: "#", 4: "X", 5: "X", 6: "X"}),
        # Lab 10 c): [q0,B]abb#aab ⊢^13 BBb#X[q2,b]ab y δ([q2,b], a) no está definida
        ("abb#aab", Outcome.REJECTED, 13, "2", "b", 5, {2: "b", 3: "#", 4: "X", 5: "a", 6: "b"}),
    ],
)
def test_lab10_hand_traces_are_reproduced(word, outcome, steps, state, cache, head, tape):
    result = simulate(lab10(), word)
    final = result.final
    assert (result.outcome, result.steps) == (outcome, steps)
    assert (final.state, final.cache, final.head, dict(final.tape)) == (state, cache, head, tape)


@pytest.mark.parametrize(
    ("word", "outcome"),
    [("ab#ab", Outcome.ACCEPTED), ("abbababa#aba", Outcome.REJECTED), ("#", Outcome.ACCEPTED), ("ab#", Outcome.REJECTED)],
)
def test_lab10_language_membership(word, outcome):
    assert simulate(lab10(), word).outcome is outcome


@pytest.mark.parametrize(
    ("word", "steps", "head", "tape"),
    [
        ("100", 5, 3, "101"),  # Lab 9 a): 101 q_halt B
        ("10011", 9, 3, "10100"),  # Lab 9 b): 101 q_halt 00
        ("11", 6, -2, "00"),  # Lab 9 c): q_halt BB00, el acarreo final se pierde
    ],
)
def test_lab9_incrementer_hand_traces_are_reproduced(word, steps, head, tape):
    result = simulate(lab9_incrementer(), word)
    final = result.final
    assert (result.outcome, result.steps, final.state, final.head) == (Outcome.ACCEPTED, steps, "qhalt", head)
    assert "".join(final.tape[i] for i in sorted(final.tape)) == tape


def test_every_configuration_is_one_step_after_the_previous_one():
    machine = lab10()
    result = simulate(machine, "aab#aab")
    ids = result.configurations
    assert len(ids) == result.steps + 1
    assert [c.step_index for c in ids] == list(range(len(ids)))
    for previous, following in zip(ids, ids[1:]):
        assert step(machine, previous) == following


def test_initial_final_state_accepts_without_transitions():
    result = simulate(tiny(Transition("s", BLANK, "a", "t", BLANK, "a", Move.R), final="s"), "a")
    assert (result.outcome, result.steps, len(result.configurations)) == (Outcome.ACCEPTED, 0, 1)


def test_missing_rule_outside_final_states_rejects():
    result = simulate(tiny(Transition("s", BLANK, "a", "t", BLANK, "X", Move.R)), "aa")
    assert (result.outcome, result.steps, result.final.state) == (Outcome.REJECTED, 1, "t")
    assert result.reason == "no hay regla para el estado 't' con caché el blanco leyendo 'a', y 't' no es final"


def test_rules_leaving_a_final_state_are_never_executed():
    machine = tiny(
        Transition("s", BLANK, "a", "f", BLANK, "X", Move.R),
        Transition("f", BLANK, "a", "s", BLANK, "a", Move.R),
    )
    result = simulate(machine, "aa")
    assert (result.outcome, result.steps, result.final.state) == (Outcome.ACCEPTED, 1, "f")


def test_endless_machine_stops_at_the_limit_without_being_rejected():
    loop = tiny(Transition("s", BLANK, "a", "s", BLANK, "a", Move.S))
    result = simulate(loop, "a", max_steps=25)
    assert (result.outcome, result.steps, len(result.configurations)) == (Outcome.LIMIT_EXCEEDED, 25, 26)
    assert result.outcome is not Outcome.REJECTED


def three_steps_to_final():
    return tiny(
        Transition("s", BLANK, "a", "t", BLANK, "a", Move.R),
        Transition("t", BLANK, BLANK, "t", "a", BLANK, Move.L),
        Transition("t", "a", "a", "f", "a", "X", Move.S),
    )


def test_reaching_final_exactly_at_the_limit_accepts():
    result = simulate(three_steps_to_final(), "a", max_steps=3)
    assert (result.outcome, result.steps) == (Outcome.ACCEPTED, 3)


def test_one_step_short_of_final_is_limit_exceeded():
    result = simulate(three_steps_to_final(), "a", max_steps=2)
    assert (result.outcome, result.steps, result.final.state) == (Outcome.LIMIT_EXCEEDED, 2, "t")


def test_cache_is_carried_between_steps():
    result = simulate(three_steps_to_final(), "a")
    assert [c.cache for c in result.configurations] == [BLANK, BLANK, "a", "a"]
    assert dict(result.final.tape) == {0: "X"}


def test_empty_input_starts_on_a_blank_cell():
    machine = tiny(Transition("s", BLANK, BLANK, "f", BLANK, "X", Move.S))
    result = simulate(machine, "")
    assert result.configurations[0].scanned is BLANK
    assert (result.outcome, dict(result.final.tape)) == (Outcome.ACCEPTED, {0: "X"})


def test_simulations_are_independent_and_repeatable():
    machine = lab10()
    first = simulate(machine, "aab#aab")
    first_ids = list(first.configurations)
    other = simulate(machine, "abb#aab")
    again = simulate(machine, "aab#aab")

    assert again == first
    assert list(first.configurations) == first_ids
    assert other.configurations[0].tape is not first.configurations[0].tape


@pytest.mark.parametrize("limit", [0, -1])
def test_max_steps_must_be_positive(limit):
    with pytest.raises(ValueError, match="max_steps"):
        simulate(lab10(), "#", max_steps=limit)


def test_input_outside_sigma_is_an_error_not_a_rejection():
    with pytest.raises(ValueError, match="fuera del alfabeto de entrada"):
        simulate(lab10(), "aXa")


def test_default_limit_is_large_enough_for_the_reference_machine():
    assert DEFAULT_MAX_STEPS >= simulate(lab10(), "abbababa#abbababa").steps

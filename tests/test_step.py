"""Transición atómica: lectura, búsqueda, escritura, estado, caché, movimiento y no aliasing."""

from pathlib import Path

import pytest

from src.input.machine_parser import parse_machine
from src.input.yaml_loader import load_yaml
from src.model.configuration import Configuration
from src.model.tape import Tape
from src.model.transition import BLANK, Move, Transition
from src.model.turing_machine import TuringMachine
from src.simulator.step import step

LAB10 = Path(__file__).resolve().parents[1] / "machines" / "examples" / "basic_machine.yaml"


def machine(*rules):
    return TuringMachine({"p", "q"}, {"a", "b"}, {"a", "b", "X", BLANK}, "p", "q", rules)


def config(word, head=0, state="p", cache=BLANK):
    return Configuration(0, state, cache, head, Tape.from_input(word).snapshot())


@pytest.mark.parametrize(("move", "head"), [(Move.L, 1), (Move.R, 3), (Move.S, 2)])
def test_move_changes_head_by_its_offset(move, head):
    m = machine(Transition("p", BLANK, "b", "q", BLANK, "b", move))
    assert step(m, config("aab", head=2)).head == head


def test_write_state_and_cache_come_from_the_rule():
    rule = Transition("p", BLANK, "a", "q", "a", "X", Move.R)
    result = step(machine(rule), config("ab"))

    assert (result.state, result.cache, result.head) == ("q", "a", 1)
    assert dict(result.tape) == {0: "X", 1: "b"}
    assert (result.step_index, result.applied) == (1, rule)


def test_rule_with_cache_value_only_matches_that_cache():
    m = machine(Transition("p", "b", "a", "q", BLANK, "a", Move.R))
    assert step(m, config("a", cache="a")) is None
    assert step(m, config("a", cache="b")).cache is BLANK


def test_writing_blank_erases_the_cell():
    m = machine(Transition("p", BLANK, "a", "q", BLANK, BLANK, Move.R))
    assert dict(step(m, config("ab")).tape) == {1: "b"}


def test_head_can_move_left_of_the_origin_and_read_blank():
    m = machine(
        Transition("p", BLANK, "a", "p", BLANK, "a", Move.L),
        Transition("p", BLANK, BLANK, "q", BLANK, "b", Move.S),
    )
    first = step(m, config("a"))
    second = step(m, first)
    assert (first.head, first.scanned) == (-1, BLANK)
    assert dict(second.tape) == {-1: "b", 0: "a"}


def test_reading_blank_after_the_input():
    m = machine(Transition("p", BLANK, BLANK, "q", BLANK, "X", Move.R))
    assert dict(step(m, config("ab", head=2)).tape) == {0: "a", 1: "b", 2: "X"}


def test_missing_rule_returns_none_without_side_effects():
    current = config("ba")
    before = (dict(current.tape), current.state, current.head)
    assert step(machine(Transition("p", BLANK, "a", "q", BLANK, "a", Move.R)), current) is None
    assert (dict(current.tape), current.state, current.head) == before


def test_previous_configuration_is_never_modified():
    current = config("aa")
    result = step(machine(Transition("p", BLANK, "a", "q", "a", "X", Move.R)), current)

    assert dict(current.tape) == {0: "a", 1: "a"}
    assert (current.state, current.cache, current.head, current.step_index) == ("p", BLANK, 0, 0)
    assert current.tape is not result.tape


def test_one_step_changes_at_most_the_scanned_cell():
    result = step(machine(Transition("p", BLANK, "b", "q", BLANK, "X", Move.R)), config("abab", head=1))
    changed = {i for i in range(-1, 5) if result.tape.get(i) != config("abab").tape.get(i)}
    assert changed == {1}


def test_first_five_moves_match_the_lab10_hand_trace():
    """Laboratorio 10, inciso b: [q0,B]aab#aab ⊢ B[q1,a]ab#aab ⊢ ... ⊢ Bab[q3,B]#Xab."""
    m, _ = parse_machine(load_yaml(LAB10))
    current = config("aab#aab", state="0")
    expected = [
        ("1", "a", 1, {1: "a", 2: "b", 3: "#", 4: "a", 5: "a", 6: "b"}),
        ("1", "a", 2, {1: "a", 2: "b", 3: "#", 4: "a", 5: "a", 6: "b"}),
        ("1", "a", 3, {1: "a", 2: "b", 3: "#", 4: "a", 5: "a", 6: "b"}),
        ("2", "a", 4, {1: "a", 2: "b", 3: "#", 4: "a", 5: "a", 6: "b"}),
        ("3", BLANK, 3, {1: "a", 2: "b", 3: "#", 4: "X", 5: "a", 6: "b"}),
    ]
    for index, (state, cache, head, tape) in enumerate(expected, start=1):
        current = step(m, current)
        assert (current.step_index, current.state, current.cache, current.head, dict(current.tape)) == (
            index, state, cache, head, tape,
        )

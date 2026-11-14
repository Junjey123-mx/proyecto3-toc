"""Contratos de los modelos: construcción, normalización, invariantes e inmutabilidad."""

from dataclasses import FrozenInstanceError

import pytest

from src.model.configuration import Configuration
from src.model.simulation_result import Outcome, SimulationResult
from src.model.transition import BLANK, Move, Transition
from src.model.turing_machine import TuringMachine

# δ([q0, B], a) = ([q1, a], B, R): primera regla del ejemplo del enunciado.
RULE = Transition("0", BLANK, "a", "1", "a", BLANK, Move.R)


def test_move_values_are_head_offsets():
    assert (Move.L.value, Move.R.value, Move.S.value) == (-1, 1, 0)
    assert Move["R"] is Move.R


def test_transition_key_includes_state_cache_and_read_symbol():
    assert RULE.key == ("0", None, "a")
    assert RULE == Transition("0", None, "a", "1", "a", None, Move.R)


def test_transition_is_immutable():
    with pytest.raises(FrozenInstanceError):
        RULE.write = "X"


def test_transition_rejects_move_that_is_not_a_move():
    with pytest.raises(TypeError, match="Move"):
        Transition("0", None, "a", "1", "a", None, "R")


def test_machine_normalizes_singular_final_state_and_collections():
    rules = [RULE]
    machine = TuringMachine(["0", "1"], ["a"], ["a", None], "0", "1", rules)
    rules.append(RULE)

    assert machine.final_states == frozenset({"1"})
    assert machine.states == frozenset({"0", "1"})
    assert machine.tape_alphabet == frozenset({"a", None})
    assert machine.transitions == (RULE,)


def test_machine_accepts_a_collection_of_final_states():
    machine = TuringMachine({"0", "1", "2"}, {"a"}, {"a", None}, "0", ["1", "2"], ())
    assert machine.final_states == frozenset({"1", "2"})


def test_machine_is_immutable():
    machine = TuringMachine({"0"}, {"a"}, {"a", None}, "0", "0", ())
    with pytest.raises(FrozenInstanceError):
        machine.initial_state = "1"


def test_configuration_tape_is_an_independent_read_only_snapshot():
    cells = {0: "a", 1: "b"}
    config = Configuration(0, "0", BLANK, 0, cells)
    cells[0] = "X"

    assert config.tape == {0: "a", 1: "b"}
    with pytest.raises(TypeError):
        config.tape[0] = "X"


def test_configuration_drops_blank_cells_and_reads_blank_outside_them():
    config = Configuration(3, "1", "a", 5, {0: "a", 1: None})
    assert dict(config.tape) == {0: "a"}
    assert config.scanned is BLANK
    assert Configuration(0, "0", BLANK, 0, {0: "a"}).scanned == "a"


def test_configuration_rejects_negative_step_index():
    with pytest.raises(ValueError, match="step_index"):
        Configuration(-1, "0", BLANK, 0, {})


def test_simulation_result_exposes_final_configuration_and_step_count():
    first = Configuration(0, "0", BLANK, 0, {0: "a"})
    second = Configuration(1, "1", "a", 1, {}, RULE)
    result = SimulationResult("a", Outcome.ACCEPTED, [first, second], "reached final state")

    assert result.final is second
    assert result.steps == 1
    assert result.configurations == (first, second)


def test_simulation_result_requires_initial_configuration():
    with pytest.raises(ValueError, match="ID_0"):
        SimulationResult("", Outcome.REJECTED, (), "no configurations")


def test_limit_exceeded_is_a_distinct_outcome_from_rejection():
    assert Outcome.LIMIT_EXCEEDED is not Outcome.REJECTED
    assert {outcome.value for outcome in Outcome} == {"ACCEPTED", "REJECTED", "LIMIT_EXCEEDED"}

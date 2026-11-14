"""Búsqueda determinista en δ por (estado, caché, símbolo leído)."""

import pytest

from src.model.transition import BLANK, Move, Transition
from src.model.turing_machine import TuringMachine

# Fragmento del Laboratorio 10 (L = {α#α}): q2 compara la lectura con la caché.
MATCH_A = Transition("q2", "a", "a", "q3", BLANK, "X", Move.L)
MATCH_B = Transition("q2", "b", "b", "q3", BLANK, "X", Move.L)
SKIP_X_A = Transition("q2", "a", "X", "q2", "a", "X", Move.R)
START_A = Transition("q0", BLANK, "a", "q1", "a", BLANK, Move.R)
FINISH = Transition("q4", BLANK, BLANK, "q5", BLANK, BLANK, Move.S)


def machine(*rules):
    return TuringMachine(
        {"q0", "q1", "q2", "q3", "q4", "q5"},
        {"a", "b", "#"},
        {"a", "b", "#", "X", BLANK},
        "q0",
        "q5",
        rules,
    )


def test_same_read_symbol_with_different_cache_selects_different_rules():
    m = machine(MATCH_A, MATCH_B)
    assert m.find_transition("q2", "a", "a") is MATCH_A
    assert m.find_transition("q2", "b", "b") is MATCH_B


def test_cache_is_part_of_the_key():
    m = machine(MATCH_A, SKIP_X_A)
    assert m.find_transition("q2", "b", "a") is None
    assert m.find_transition("q2", "a", "X") is SKIP_X_A


def test_state_is_part_of_the_key():
    m = machine(START_A)
    assert m.find_transition("q0", BLANK, "a") is START_A
    assert m.find_transition("q1", BLANK, "a") is None


def test_blank_cache_and_blank_read_are_valid_key_components():
    m = machine(FINISH)
    assert m.find_transition("q4", BLANK, BLANK) is FINISH


def test_missing_rule_returns_none_instead_of_an_implicit_rule():
    assert machine().find_transition("q0", BLANK, "a") is None


def test_found_rule_keeps_its_move_and_outputs():
    left = machine(MATCH_A).find_transition("q2", "a", "a")
    right = machine(SKIP_X_A).find_transition("q2", "a", "X")
    stay = machine(FINISH).find_transition("q4", BLANK, BLANK)
    assert (left.move, right.move, stay.move) == (Move.L, Move.R, Move.S)
    assert (left.next_state, left.next_cache, left.write) == ("q3", BLANK, "X")


def test_identical_duplicate_rules_are_rejected_with_positions():
    with pytest.raises(ValueError, match=r"reglas 0 y 2 están duplicadas"):
        machine(START_A, MATCH_A, START_A)


def test_conflicting_rules_for_the_same_key_are_rejected():
    conflicting = Transition("q2", "a", "a", "q2", "a", "a", Move.R)
    with pytest.raises(ValueError, match=r"reglas 0 y 1 están en conflicto"):
        machine(MATCH_A, conflicting)


def test_declared_order_is_preserved_and_source_list_is_not_modified():
    rules = [FINISH, START_A, MATCH_A]
    m = machine(*rules)
    assert m.transitions == (FINISH, START_A, MATCH_A)
    assert rules == [FINISH, START_A, MATCH_A]

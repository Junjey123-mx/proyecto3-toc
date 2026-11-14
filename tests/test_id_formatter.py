"""Formato de IDs: notación de los laboratorios, blancos, cabezal en los extremos y reglas."""

from pathlib import Path

import pytest

from src.input.machine_parser import parse_machine
from src.input.yaml_loader import load_yaml
from src.model.transition import BLANK, Move, Transition
from src.model.turing_machine import TuringMachine
from src.output.id_formatter import NO_RULE, format_id, format_id_lines
from src.simulator.engine import simulate
from src.simulator.trace import TraceEntry, build_trace
from src.utils.notation import blank_glyph, format_control, format_rule, show_symbol

LAB10 = Path(__file__).resolve().parents[1] / "machines" / "examples" / "basic_machine.yaml"


def lab10():
    return parse_machine(load_yaml(LAB10))[0]


def entry(tape, head, state="q", cache=BLANK):
    return TraceEntry(0, state, cache, head, tape, None)


def test_lab10_hand_trace_ids_are_reproduced():
    """Laboratorio 10 b): [q0,B]aab#aab ⊢ B[q1,a]ab#aab ⊢ … ⊢ Bab[q3,B]#Xab ⊢* BBB#XXXB[q5,B]B."""
    trace = build_trace(simulate(lab10(), "aab#aab"))
    ids = [format_id(e, 7) for e in trace.entries]
    assert ids[:6] == [
        "[0,B]aab#aab",
        "B[1,a]ab#aab",
        "Ba[1,a]b#aab",
        "Bab[1,a]#aab",
        "Bab#[2,a]aab",
        "Bab[3,B]#Xab",
    ]
    assert ids[-1] == "BBB#XXXB[5,B]B"


def test_lab10_rejected_trace_ends_like_the_hand_trace():
    """Laboratorio 10 c): ⊢^13 BBb#X[q2,b]ab."""
    trace = build_trace(simulate(lab10(), "abb#aab"))
    assert format_id(trace.final, 7) == "BBb#X[2,b]ab"


def test_head_left_of_the_content_shows_the_blanks_in_between():
    """Laboratorio 9, ej. 2 c): q_halt BB00 (cabezal en -2)."""
    assert format_id(entry({0: "0", 1: "0"}, -2, "qhalt"), 2) == "[qhalt,B]BB00"


def test_head_right_of_the_content_shows_the_scanned_blank():
    assert format_id(entry({0: "a", 1: "b"}, 2, "q1"), 2) == "ab[q1,B]B"
    assert format_id(entry({0: "a"}, 3, "q1"), 1) == "aBB[q1,B]B"


def test_intermediate_blanks_are_visible():
    assert format_id(entry({0: "a", 3: "b"}, 1, "p"), 4) == "a[p,B]BBb"


def test_cache_value_appears_inside_the_control_tuple():
    assert format_id(entry({0: "1", 1: "0"}, 1, "q1", cache="1"), 2) == "1[q1,1]0"


def test_empty_input_shows_only_the_scanned_blank():
    assert format_id(entry({}, 0, "q0"), 0) == "[q0,B]B"


def test_custom_blank_glyph():
    assert format_id(entry({1: "a"}, 0, "q0"), 2, blank="□") == "[q0,□]□a"


def test_blank_glyph_avoids_ambiguity_with_symbol_b():
    plain = TuringMachine({"s"}, {"a"}, {"a", BLANK}, "s", "s", ())
    with_b = TuringMachine({"s"}, {"a"}, {"a", "B", BLANK}, "s", "s", ())
    cache_b = TuringMachine({"s"}, {"a"}, {"a", BLANK}, "s", "s", (Transition("s", "B", "a", "s", BLANK, "a", Move.R),))
    assert (blank_glyph(plain), blank_glyph(with_b), blank_glyph(cache_b)) == ("B", "□", "□")


def test_rule_notation_matches_the_statement():
    rule = Transition("q0", BLANK, "a", "q1", "a", BLANK, Move.R)
    assert format_rule(rule) == "δ([q0, B], a) = ([q1, a], B, R)"
    assert format_control("q0", BLANK) == "[q0,B]"
    assert format_control("q0", "x", compact=False) == "[q0, x]"
    assert (show_symbol(BLANK), show_symbol("X")) == ("B", "X")


def test_table_has_header_and_one_row_per_id_with_its_rule():
    trace = build_trace(simulate(lab10(), "ab#ab"))
    lines = format_id_lines(trace)
    assert len(lines) == trace.steps + 2
    assert lines[0].split() == ["Paso", "ID", "Transición", "aplicada"]
    assert lines[1].split() == ["0", "[0,B]ab#ab", NO_RULE]
    for line, e in zip(lines[2:], trace.entries[1:]):
        assert line.split(maxsplit=2) == [str(e.step), format_id(e, 5), format_rule(e.applied)]


def test_each_row_can_be_rebuilt_from_the_previous_one():
    """Leer la ID previa y la regla basta para obtener la siguiente ID, como en una tabla manual."""
    trace = build_trace(simulate(lab10(), "abb#aab"))
    for previous, current in zip(trace.entries, trace.entries[1:]):
        rule = current.applied
        assert (rule.state, rule.cache, rule.read) == (previous.state, previous.cache, previous.scanned)
        assert f"[{rule.next_state},{show_symbol(rule.next_cache)}]" in format_id(current, 7)


def test_ids_are_never_truncated():
    loop = TuringMachine({"s", "f"}, {"a"}, {"a", BLANK}, "s", "f", (
        Transition("s", BLANK, "a", "s", BLANK, "a", Move.R),
        Transition("s", BLANK, BLANK, "f", BLANK, BLANK, Move.S),
    ))
    word = "a" * 300
    trace = build_trace(simulate(loop, word))
    assert format_id(trace.final, 300) == word + "[f,B]B"


def test_formatting_does_not_modify_the_trace():
    trace = build_trace(simulate(lab10(), "aab#aab"))
    before = [(e.state, e.cache, e.head, dict(e.tape)) for e in trace.entries]
    format_id_lines(trace)
    assert [(e.state, e.cache, e.head, dict(e.tape)) for e in trace.entries] == before


@pytest.mark.parametrize("head", [-3, 0, 2, 5])
def test_exactly_one_control_tuple_per_id(head):
    assert format_id(entry({0: "a", 1: "b", 2: "a"}, head), 3).count("[") == 1

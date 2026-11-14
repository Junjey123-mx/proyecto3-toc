"""Reporte por cadena y resumen: veredicto exacto, cinta final, pasos e IDs completas."""

from pathlib import Path

from src.input.machine_parser import parse_machine
from src.input.yaml_loader import load_yaml
from src.model.simulation_result import Outcome
from src.model.transition import BLANK, Move, Transition
from src.model.turing_machine import TuringMachine
from src.output.id_formatter import format_id_lines
from src.output.result_formatter import (
    BLANK_TAPE,
    EMPTY_WORD,
    format_outcome,
    format_result,
    format_summary,
    show_word,
)
from src.simulator.engine import simulate
from src.simulator.trace import build_trace

LAB10 = Path(__file__).resolve().parents[1] / "machines" / "examples" / "basic_machine.yaml"


def lab10():
    return parse_machine(load_yaml(LAB10))[0]


def trace_of(word, machine=None, **kwargs):
    return build_trace(simulate(machine or lab10(), word, **kwargs))


def field(lines, name):
    """Valor de una línea «Nombre: valor» del reporte."""
    prefix = f"{name}:"
    return next(line[len(prefix):].strip() for line in lines if line.startswith(prefix))


def loop_machine():
    return TuringMachine({"s", "f"}, {"a"}, {"a", BLANK}, "s", "f", (Transition("s", BLANK, "a", "s", BLANK, "a", Move.S),))


def test_accepted_report_has_header_verdict_and_final_configuration():
    lines = format_result(trace_of("aab#aab"), 1, 5)
    assert lines[0] == "=== Cadena 1 de 5: 'aab#aab' (longitud 7) ==="
    assert field(lines, "Resultado") == "ACCEPTED (aceptada)"
    assert field(lines, "Motivo") == "alcanzó el estado final '5'"
    assert (field(lines, "Pasos"), field(lines, "Estado final"), field(lines, "Caché final")) == ("32", "5", "B")
    assert (field(lines, "Cabezal final"), field(lines, "Cinta final")) == ("8", "#XXX")
    assert field(lines, "ID final") == "BBB#XXXB[5,B]B"


def test_rejected_report_shows_the_missing_rule():
    lines = format_result(trace_of("abb#aab"))
    assert lines[0] == "=== Cadena: 'abb#aab' (longitud 7) ==="
    assert field(lines, "Resultado") == "REJECTED (rechazada)"
    assert "no hay regla para el estado '2' con caché 'b' leyendo 'a'" in field(lines, "Motivo")


def test_limit_is_never_reported_as_a_rejection():
    lines = format_result(trace_of("a", loop_machine(), max_steps=4))
    verdict = field(lines, "Resultado")
    assert verdict.startswith("LIMIT_EXCEEDED")
    assert "no es un rechazo" in verdict
    assert "REJECTED" not in "\n".join(lines) and "(rechazada)" not in "\n".join(lines)
    assert field(lines, "Pasos") == "4"


def test_report_contains_the_complete_id_table():
    trace = trace_of("abbababa#aba")
    lines = format_result(trace)
    table = [f"  {line}" for line in format_id_lines(trace)]
    start = lines.index(table[0])
    assert lines[start:] == table
    assert len(table) == trace.steps + 2
    assert lines[start - 1] == f"Descripciones instantáneas (ID_0 a ID_{trace.steps}):"


def test_final_tape_view_is_included():
    lines = format_result(trace_of("abb#aab"))
    assert any(line.startswith("posición") for line in lines)
    assert any(line.startswith("cabezal") and line.rstrip().endswith("^") for line in lines)


def test_blank_tape_and_empty_word_are_explicit():
    eraser = TuringMachine({"s", "f"}, {"a"}, {"a", BLANK}, "s", "f", (
        Transition("s", BLANK, "a", "s", BLANK, BLANK, Move.R),
        Transition("s", BLANK, BLANK, "f", BLANK, BLANK, Move.S),
    ))
    lines = format_result(trace_of("aa", eraser))
    assert field(lines, "Cinta final") == BLANK_TAPE
    assert format_result(trace_of("", eraser))[0] == f"=== Cadena: {EMPTY_WORD} (longitud 0) ==="
    assert (show_word(""), show_word("ab")) == (EMPTY_WORD, "'ab'")


def test_outcome_labels_use_the_enum_values():
    assert format_outcome(Outcome.ACCEPTED) == "ACCEPTED (aceptada)"
    assert format_outcome(Outcome.REJECTED) == "REJECTED (rechazada)"
    assert format_outcome(Outcome.LIMIT_EXCEEDED).startswith("LIMIT_EXCEEDED (sin veredicto")


def test_summary_has_one_distinguishable_row_per_word():
    machine = lab10()
    words = ["aab#aab", "ab#ab", "abbababa#aba", "abb#aab", "#"]
    lines = format_summary([trace_of(word, machine) for word in words])
    assert lines[0].split() == ["#", "Cadena", "Longitud", "Resultado", "Pasos", "Cinta", "final"]
    rows = [line.split() for line in lines[1:]]
    assert rows == [
        ["1", "aab#aab", "7", "ACCEPTED", "32", "#XXX"],
        ["2", "ab#ab", "5", "ACCEPTED", "18", "#XX"],
        ["3", "abbababa#aba", "12", "REJECTED", "47", "ababa#XXa"],
        ["4", "abb#aab", "7", "REJECTED", "13", "b#Xab"],
        ["5", "#", "1", "ACCEPTED", "2", "#"],
    ]


def test_summary_marks_limit_exceeded():
    lines = format_summary([trace_of("a", loop_machine(), max_steps=2)])
    assert lines[1].split()[:5] == ["1", "a", "1", "LIMIT_EXCEEDED", "2"]


def test_condensed_tape_view_keeps_the_full_ids():
    trace = trace_of("abbababa#aba")
    lines = format_result(trace, max_tape_cells=3)
    assert "…" in next(line for line in lines if line.startswith("posición"))
    assert all("…" not in line for line in format_id_lines(trace))
    assert [f"  {line}" for line in format_id_lines(trace)] == lines[-(trace.steps + 2):]


def test_formatting_does_not_modify_the_trace():
    trace = trace_of("aab#aab")
    before = [(e.state, e.cache, e.head, dict(e.tape)) for e in trace.entries]
    format_result(trace)
    format_summary([trace])
    assert [(e.state, e.cache, e.head, dict(e.tape)) for e in trace.entries] == before

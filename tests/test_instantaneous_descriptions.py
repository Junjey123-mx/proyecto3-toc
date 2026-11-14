"""Traza de IDs: secuencia completa, snapshots independientes y verificación de cada paso."""

from pathlib import Path

import pytest

from src.input.machine_parser import parse_machine
from src.input.machine_validator import validate_machine
from src.input.yaml_loader import load_yaml
from src.model.configuration import Configuration
from src.model.simulation_result import Outcome, SimulationResult
from src.model.transition import BLANK, Move, Transition
from src.model.turing_machine import TuringMachine
from src.simulator.engine import simulate
from src.simulator.trace import Trace, TraceEntry, TraceError, build_trace

LAB10 = Path(__file__).resolve().parents[1] / "machines" / "examples" / "basic_machine.yaml"


def lab10():
    machine, strings = parse_machine(load_yaml(LAB10))
    validate_machine(machine, strings)
    return machine


def tiny(*rules, final="f"):
    return TuringMachine({"s", "t", "f"}, {"a"}, {"a", "X", BLANK}, "s", final, rules)


def test_trace_has_one_entry_per_configuration_and_steps_plus_one():
    result = simulate(lab10(), "aab#aab")
    trace = build_trace(result)
    assert len(trace.entries) == result.steps + 1 == trace.steps + 1 == 33
    assert [entry.step for entry in trace.entries] == list(range(33))
    assert (trace.word, trace.outcome, trace.reason) == (result.word, result.outcome, result.reason)


def test_entries_copy_every_field_of_the_configurations():
    result = simulate(lab10(), "abb#aab")
    for config, entry in zip(result.configurations, build_trace(result).entries):
        assert (entry.step, entry.state, entry.cache, entry.head, entry.applied) == (
            config.step_index, config.state, config.cache, config.head, config.applied,
        )
        assert dict(entry.tape) == dict(config.tape)
        assert entry.scanned == config.scanned


def test_zero_step_trace_contains_only_id0():
    result = simulate(tiny(Transition("s", BLANK, "a", "t", BLANK, "a", Move.R), final="s"), "a")
    trace = build_trace(result)
    assert (trace.steps, len(trace.entries), trace.final.applied) == (0, 1, None)
    assert trace.final is trace.entries[0]


def test_long_trace_is_not_truncated():
    loop = tiny(Transition("s", BLANK, "a", "s", BLANK, "a", Move.S))
    trace = build_trace(simulate(loop, "a", max_steps=500))
    assert (trace.outcome, trace.steps, len(trace.entries)) == (Outcome.LIMIT_EXCEEDED, 500, 501)


def test_entry_tape_is_a_read_only_copy():
    result = simulate(lab10(), "ab#ab")
    entry = build_trace(result).entries[0]
    assert entry.tape is not result.configurations[0].tape
    with pytest.raises(TypeError):
        entry.tape[0] = "X"


def test_building_a_trace_never_changes_previous_ids():
    machine = lab10()
    result = simulate(machine, "aab#aab")
    before = [(c.state, c.cache, c.head, dict(c.tape)) for c in result.configurations]
    trace = build_trace(result)
    again = build_trace(result)
    assert [(c.state, c.cache, c.head, dict(c.tape)) for c in result.configurations] == before
    assert again == trace
    assert [dict(e.tape) for e in trace.entries] == [tape for *_, tape in before]


def test_changing_cache_is_recorded_in_each_entry():
    machine = tiny(
        Transition("s", BLANK, "a", "t", BLANK, "a", Move.R),
        Transition("t", BLANK, BLANK, "t", "a", BLANK, Move.L),
        Transition("t", "a", "a", "f", "a", "X", Move.S),
    )
    trace = build_trace(simulate(machine, "a"))
    assert [entry.cache for entry in trace.entries] == [BLANK, BLANK, "a", "a"]
    assert [entry.scanned for entry in trace.entries] == ["a", BLANK, "a", "X"]


def test_negative_head_positions_are_kept_and_inside_the_span():
    machine = tiny(
        Transition("s", BLANK, "a", "s", BLANK, "a", Move.L),
        Transition("s", BLANK, BLANK, "t", BLANK, BLANK, Move.L),
        Transition("t", BLANK, BLANK, "f", BLANK, "X", Move.S),
    )
    trace = build_trace(simulate(machine, "a"))
    assert [entry.head for entry in trace.entries] == [0, -1, -2, -2]
    assert dict(trace.final.tape) == {-2: "X", 0: "a"}
    assert trace.entries[1].span(1) == (-1, 0)
    assert trace.final.span(1) == (-2, 0)


def test_span_keeps_erased_input_and_reaches_the_head():
    """Laboratorio 10 b), ID final BBB#XXXB[q5,B]B: posiciones 0..8."""
    trace = build_trace(simulate(lab10(), "aab#aab"))
    assert trace.final.span(len("aab#aab")) == (0, 8)


def test_span_of_empty_input_is_the_head_cell():
    machine = tiny(Transition("s", BLANK, BLANK, "f", BLANK, BLANK, Move.R))
    trace = build_trace(simulate(machine, ""))
    assert [entry.span(0) for entry in trace.entries] == [(0, 0), (1, 1)]


def test_consecutive_words_produce_independent_traces():
    machine = lab10()
    first = build_trace(simulate(machine, "aab#aab"))
    second = build_trace(simulate(machine, "abb#aab"))
    third = build_trace(simulate(machine, "aab#aab"))
    assert third == first
    assert first.entries[0].tape is not second.entries[0].tape
    assert (first.outcome, second.outcome) == (Outcome.ACCEPTED, Outcome.REJECTED)
    assert dict(second.entries[0].tape) == dict(enumerate("abb#aab"))


def forged(*configs):
    return SimulationResult("a", Outcome.ACCEPTED, configs, "prueba")


def test_rejects_a_rule_that_does_not_match_the_previous_id():
    wrong = Transition("t", BLANK, "a", "f", BLANK, "a", Move.R)
    first = Configuration(0, "s", BLANK, 0, {0: "a"})
    second = Configuration(1, "f", BLANK, 1, {0: "a"}, wrong)
    with pytest.raises(TraceError, match="no corresponde"):
        build_trace(forged(first, second))


def test_rejects_an_id_that_is_not_the_result_of_its_rule():
    rule = Transition("s", BLANK, "a", "f", BLANK, "X", Move.R)
    first = Configuration(0, "s", BLANK, 0, {0: "a"})
    second = Configuration(1, "f", BLANK, 1, {0: "a"}, rule)  # debía escribir X
    with pytest.raises(TraceError, match="no es el resultado"):
        build_trace(forged(first, second))


def test_rejects_skipped_steps_and_missing_rules():
    rule = Transition("s", BLANK, "a", "f", BLANK, "a", Move.R)
    first = Configuration(0, "s", BLANK, 0, {0: "a"})
    with pytest.raises(TraceError, match="consecutivos"):
        build_trace(forged(first, Configuration(2, "f", BLANK, 1, {0: "a"}, rule)))
    with pytest.raises(TraceError, match="falta la regla"):
        build_trace(forged(first, Configuration(1, "f", BLANK, 1, {0: "a"})))
    with pytest.raises(TraceError, match="ID_0"):
        build_trace(forged(Configuration(0, "s", BLANK, 0, {0: "a"}, rule)))


def test_trace_requires_id0():
    with pytest.raises(TraceError):
        Trace("a", Outcome.ACCEPTED, "x", ())


def test_entry_drops_blank_cells():
    entry = TraceEntry(0, "s", BLANK, 0, {0: "a", 1: BLANK}, None)
    assert dict(entry.tape) == {0: "a"}

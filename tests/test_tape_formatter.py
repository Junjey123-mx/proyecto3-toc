"""Vista de la cinta: posiciones, cabezal, blancos, extremos negativos y modo condensado."""

import re

import pytest

from src.model.transition import BLANK
from src.output.tape_formatter import ELLIPSIS, HEAD_MARK, render_entry_tape, render_tape, tape_contents
from src.simulator.trace import TraceEntry


def columns(lines):
    """Separa las tres líneas en columnas sin la etiqueta."""
    return [line.split()[1:] for line in lines]


def head_column(lines):
    """Índice de columna de la marca del cabezal, medido por su desplazamiento en el texto."""
    offset = lines[2].index(HEAD_MARK)
    ends = [match.end() - 1 for match in re.finditer(r"\S+", lines[0])][1:]
    return ends.index(offset)


def test_contents_spans_first_to_last_non_blank_cell():
    assert tape_contents({-1: "1", 0: "0", 1: "0"}) == "100"
    assert tape_contents({3: "a", 4: "b"}) == "ab"


def test_contents_shows_inner_blanks_and_empty_tape():
    assert tape_contents({0: "1", 2: "1"}) == "1B1"
    assert tape_contents({0: "1", 2: "1"}, blank="□") == "1□1"
    assert tape_contents({}) == ""


def test_positions_symbols_and_head_are_aligned():
    lines = render_tape({0: "a", 1: "b", 2: "a"}, 1, 0, 2)
    assert [line.split()[0] for line in lines] == ["posición", "cinta", "cabezal"]
    pos, cells, _ = columns(lines)
    assert (pos, cells) == (["0", "1", "2"], ["a", "b", "a"])
    assert head_column(lines) == 1


def test_negative_positions_and_head_on_the_new_leftmost_cell():
    lines = render_tape({-1: "1", 0: "0", 1: "0"}, -1, -1, 1)
    pos, cells, marks = columns(lines)
    assert (pos, cells, marks) == (["-1", "0", "1"], ["1", "0", "0"], [HEAD_MARK])
    assert head_column(lines) == 0


def test_range_grows_to_include_the_head():
    lines = render_tape({0: "a"}, 3, 0, 0)
    pos, cells, _ = columns(lines)
    assert (pos, cells) == (["0", "1", "2", "3"], ["a", "B", "B", "B"])
    assert head_column(lines) == 3


def test_blank_tape_shows_the_scanned_blank():
    assert columns(render_tape({}, 0, 0, 0)) == [["0"], ["B"], [HEAD_MARK]]


def test_full_view_shows_every_cell_of_the_range():
    tape = {i: "a" for i in range(40)}
    pos, cells, _ = columns(render_tape(tape, 0, 0, 39))
    assert pos == [str(i) for i in range(40)] and cells == ["a"] * 40


def test_condensed_view_is_marked_and_keeps_the_head():
    tape = {i: "a" for i in range(20)}
    lines = render_tape(tape, 10, 0, 19, max_cells=7)
    pos, cells, _ = columns(lines)
    assert pos == [ELLIPSIS, "7", "8", "9", "10", "11", "12", "13", ELLIPSIS]
    assert cells[0] == cells[-1] == ELLIPSIS
    assert pos[head_column(lines)] == "10"


def test_condensed_view_near_an_edge_only_marks_the_cut_side():
    pos, _, _ = columns(render_tape({i: "a" for i in range(20)}, 0, 0, 19, max_cells=4))
    assert pos == ["0", "1", "2", "3", ELLIPSIS]
    pos, _, _ = columns(render_tape({i: "a" for i in range(20)}, 19, 0, 19, max_cells=4))
    assert pos == [ELLIPSIS, "16", "17", "18", "19"]


def test_condensed_view_is_not_applied_when_the_range_fits():
    assert render_tape({0: "a"}, 0, 0, 2, max_cells=10) == render_tape({0: "a"}, 0, 0, 2)


def test_max_cells_must_be_positive():
    with pytest.raises(ValueError):
        render_tape({}, 0, 0, 0, max_cells=0)


def test_output_is_plain_text_without_ansi_or_trailing_spaces():
    lines = render_tape({-12: "x", 0: "a"}, 5, -12, 0)
    assert all("\x1b" not in line and line == line.rstrip() for line in lines)
    assert len(lines[0]) == len(lines[1])


def test_entry_view_uses_the_id_span():
    entry = TraceEntry(4, "q", BLANK, -2, {0: "0", 1: "0"}, None)
    pos, cells, _ = columns(render_entry_tape(entry, 2))
    assert (pos, cells) == (["-2", "-1", "0", "1"], ["B", "B", "0", "0"])


def test_rendering_does_not_modify_the_tape():
    tape = {0: "a", 1: "b"}
    render_tape(tape, 5, 0, 1, max_cells=2)
    tape_contents(tape)
    assert tape == {0: "a", 1: "b"}

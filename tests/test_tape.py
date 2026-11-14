"""Cinta dispersa: blanco implícito, escritura, borrado, índices negativos y snapshots."""

import pytest

from src.model.tape import Tape
from src.model.transition import BLANK


def test_empty_tape_reads_blank_everywhere():
    tape = Tape()
    assert [tape.read(index) for index in (-1, 0, 7)] == [BLANK, BLANK, BLANK]
    assert tape.snapshot() == {}


def test_input_starts_at_zero_and_is_surrounded_by_blanks():
    tape = Tape.from_input("aab")
    assert [tape.read(index) for index in range(-1, 4)] == [BLANK, "a", "a", "b", BLANK]


def test_empty_input_leaves_head_cell_blank():
    tape = Tape.from_input("")
    assert tape.read(0) is BLANK
    assert tape.snapshot() == {}


def test_write_and_overwrite():
    tape = Tape.from_input("a")
    tape.write(0, "X")
    tape.write(0, "Y")
    tape.write(1, "b")
    assert tape.snapshot() == {0: "Y", 1: "b"}


def test_writing_blank_erases_the_cell():
    tape = Tape.from_input("ab")
    tape.write(0, BLANK)
    tape.write(5, BLANK)
    assert tape.read(0) is BLANK
    assert tape.snapshot() == {1: "b"}


def test_tape_grows_in_both_directions_including_negative_positions():
    tape = Tape.from_input("1")
    tape.write(-1, "1")
    tape.write(-3, "#")
    tape.write(10, "X")
    assert tape.read(-1) == "1"
    assert tape.read(-2) is BLANK
    assert tape.snapshot() == {-3: "#", -1: "1", 0: "1", 10: "X"}


def test_snapshot_is_independent_and_read_only():
    tape = Tape.from_input("ab")
    snapshot = tape.snapshot()
    tape.write(0, "X")

    assert snapshot == {0: "a", 1: "b"}
    with pytest.raises(TypeError):
        snapshot[0] = "X"


def test_constructor_copies_cells_and_drops_blanks():
    cells = {0: "a", 1: None}
    tape = Tape(cells)
    cells[0] = "X"
    assert tape.snapshot() == {0: "a"}

import pytest

import rich
import gomoku.io as io
from gomoku.board import Board


def test_valid_input():
    assert io.valid_input("a1")
    assert io.valid_input("H15")
    assert io.valid_input("c09")

    assert not io.valid_input("1a")
    assert not io.valid_input("aa1")
    assert not io.valid_input("a")


def test_board_coords_to_xy_ok_values():
    b = Board(size=15, win_len=5)
    assert io.board_coords_to_xy("a1", b) == (0, 0)
    assert io.board_coords_to_xy("C2", b) == (1, 2)
    assert io.board_coords_to_xy("o15", b) == (14, 14)


def test_board_coords_to_xy_invalid_values():
    b = Board(size=5, win_len=4)

    assert io.board_coords_to_xy("z9", b) is False
    assert io.board_coords_to_xy("11", b) is False
    assert io.board_coords_to_xy("a0", b) is False
    assert io.board_coords_to_xy("f1", b) is False

    b.place(0, 0)
    assert io.board_coords_to_xy("a1", b) is False


def test_create_table_basic_shape():
    b = Board(size=4, win_len=3)
    table = io.create_table(b)

    # row/col labels included
    assert len(table.columns) == 5
    assert len(table.rows) == 5


def test_create_table_highlight_last_move():
    b = Board(size=4, win_len=3)
    b.place(1, 2)

    table = io.create_table(b)
    assert table.rows[2].style == "orange_red1"
    assert table.columns[3].style == "orange_red1"

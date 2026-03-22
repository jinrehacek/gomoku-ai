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


def test_xy_to_board_coords():
    assert io.xy_to_board_coords(0, 0) == "a1"
    assert io.xy_to_board_coords(1, 2) == "c2"
    assert io.xy_to_board_coords(14, 14) == "o15"

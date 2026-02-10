import pytest
from gomoku.board import Board
from gomoku.engine import get_candidate_moves, _immediate_neighbors


def test_get_immediate_neighbors():
    size = 5
    b = Board(size=size, win_len=4)
    # neighbors for (2, 3)
    NEIGHBORS = [(1, 3), (3, 3), (1, 2), (1, 4), (2, 2), (2, 4), (3, 2), (3, 4)]
    output = set()
    should = set(NEIGHBORS)
    for neighbor in _immediate_neighbors(2, 3, distance=1, board_size=size):
        output.add(neighbor)
    assert should == output


def test_get_immediate_neighbors_corner():
    size = 5
    # we are checking dist = 2 for (0, 0)
    # 00 01 02
    # 10 11 12
    # 20 21 22
    NEIGHBORS = [(0, 1), (1, 1), (1, 0), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0)]
    should = set(NEIGHBORS)
    output = set()
    for neighbor in _immediate_neighbors(0, 0, distance=2, board_size=size):
        output.add(neighbor)
    assert should == output


def test_get_candidate_moves():
    size = 5
    b = Board(size=size, win_len=4)
    b.place(0, 0)
    OUT = [(0, 1), (1, 1), (1, 0)]
    should_out = set(OUT)
    got_out = set(get_candidate_moves(b, 1))
    assert got_out == should_out

    b.place(0, 1)
    OUT = [(1, 0), (1, 1), (1, 2), (0, 2)]
    should_out = set(OUT)
    got_out = set(get_candidate_moves(b, 1))
    assert got_out == should_out

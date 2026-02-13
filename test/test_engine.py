import pytest
from gomoku.board import Board
from gomoku.engine import get_candidate_moves, _immediate_neighbors, eval_line, prepare_patterns, shortest_pattern, eval_board


def test_get_immediate_neighbors():
    size = 5
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


MOCK_PATTERNS = [
    (10, (1, 1, 0)),
    (50, (0, 1, 1, 1, 0)),
]


def test_shortest_pattern():
    assert shortest_pattern(MOCK_PATTERNS) == 3


MIRRORED_MULTICULTURAL_PATTERNS = [
    (10, (1, 1, 0)),
    (10, (0, 1, 1)),
    (50, (0, 1, 1, 1, 0)),
    (-10, (2, 2, 0)),
    (-10, (0, 2, 2)),
    (-50, (0, 2, 2, 2, 0)),
]


def test_prepare_patterns():
    got = set(prepare_patterns(MOCK_PATTERNS))
    should = set(MIRRORED_MULTICULTURAL_PATTERNS)
    assert got == should


def test_eval_line():
    patterns = prepare_patterns(MOCK_PATTERNS)
    sp = shortest_pattern(patterns)
    assert eval_line([0, 1, 1, 1, 0], patterns, sp) == 70  # 10 + 50 + 10
    assert eval_line([0, 2, 2, 2, 0], patterns, sp) == -70  # -10 -50 -10
    assert eval_line([1, 1, 0, 0, 0], patterns, sp) == 10
    assert eval_line([0, 0, 0, 0, 0], patterns, sp) == 0
    assert eval_line([0, 1, 1, 0], patterns, sp) == 20  # 10 + 10
    assert eval_line([1, 1], patterns, sp) == 0  # moc kratke


def test_eval_board():
    patterns = prepare_patterns(MOCK_PATTERNS)
    sp = shortest_pattern(patterns)

    b = Board(size=4, win_len=3)
    assert eval_board(b, patterns, sp) == 0

    b = Board(size=4, win_len=3)
    b.data[0] = [1, 0, 0, 0]
    assert eval_board(b, patterns, sp) == 0

    b = Board(size=4, win_len=3)
    b.data[0] = [1, 1, 0, 0]
    assert eval_board(b, patterns, sp) == 10

    b = Board(size=4, win_len=3)
    b.data[0] = [0, 1, 1, 0]
    assert eval_board(b, patterns, sp) == 20  # 10 + 10

    b = Board(size=5, win_len=3)
    b.data[0] = [1, 1, 0, 0, 0]
    b.data[1] = [2, 2, 0, 0, 0]
    assert eval_board(b, patterns, sp) == 0  # 10 + -10

    # column [1,1,0,0]
    b = Board(size=4, win_len=3)
    b.data[0][0] = 1
    b.data[1][0] = 1
    assert eval_board(b, patterns, sp) == 10

    # diagonala \ [1,1,0,0]
    b = Board(size=4, win_len=3)
    b.data[0][0] = 1
    b.data[1][1] = 1
    assert eval_board(b, patterns, sp) == 10

    # diagonala / [1,1,0]
    b = Board(size=4, win_len=3)
    b.data[2][0] = 1
    b.data[1][1] = 1
    assert eval_board(b, patterns, sp) == 10

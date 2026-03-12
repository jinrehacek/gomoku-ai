import pytest
from gomoku.board import Board
from gomoku.engine import (
    get_candidate_moves,
    _immediate_neighbors,
    eval_line,
    prepare_patterns,
    eval_board,
    minimax,
    get_best_move,
    COMPLETE_PATTERNS,
    WIN_CONSTANT,
)


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


def test_eval_line():
    patterns = prepare_patterns(MOCK_PATTERNS)
    assert eval_line([0, 1, 1, 1, 0], patterns) == 70  # 10 + 50 + 10
    assert eval_line([0, 2, 2, 2, 0], patterns) == -70  # -10 -50 -10
    assert eval_line([1, 1, 0, 0, 0], patterns) == 10
    assert eval_line([0, 0, 0, 0, 0], patterns) == 0
    assert eval_line([0, 1, 1, 0], patterns) == 20  # 10 + 10
    assert eval_line([1, 1], patterns) == 0  # moc kratke


def test_eval_board():
    patterns = prepare_patterns(MOCK_PATTERNS)

    b = Board(size=4, win_len=3)
    assert eval_board(b, patterns) == 0

    b = Board(size=4, win_len=3)
    b.data[0] = [1, 0, 0, 0]
    assert eval_board(b, patterns) == 0

    b = Board(size=4, win_len=3)
    b.data[0] = [1, 1, 0, 0]
    assert eval_board(b, patterns) == 10

    b = Board(size=4, win_len=3)
    b.data[0] = [0, 1, 1, 0]
    assert eval_board(b, patterns) == 20  # 10 + 10

    b = Board(size=5, win_len=3)
    b.data[0] = [1, 1, 0, 0, 0]
    b.data[1] = [2, 2, 0, 0, 0]
    assert eval_board(b, patterns) == 0  # 10 + -10

    # column [1,1,0,0]
    b = Board(size=4, win_len=3)
    b.data[0][0] = 1
    b.data[1][0] = 1
    assert eval_board(b, patterns) == 10

    # diagonala \ [1,1,0,0]
    b = Board(size=4, win_len=3)
    b.data[0][0] = 1
    b.data[1][1] = 1
    assert eval_board(b, patterns) == 10

    # diagonala / [1,1,0]
    b = Board(size=4, win_len=3)
    b.data[2][0] = 1
    b.data[1][1] = 1
    assert eval_board(b, patterns) == 10


def test_minimax_zero_depth():
    b = Board(size=5, win_len=4)
    b.data[0] = [1, 1, 0, 0, 0]

    # je stejne jako eval_board - aka jede jen heuristika
    expected = eval_board(b, COMPLETE_PATTERNS)
    assert minimax(b, depth=0, player=0) == expected
    assert minimax(b, depth=0, player=1) == expected


def test_minimax_white_wins():
    b = Board(size=7, win_len=5)
    for i in range(5):
        b.data[0][i] = 1
    assert minimax(b, depth=1, player=1) == WIN_CONSTANT


def test_minimax_black_wins():
    b = Board(size=7, win_len=5)
    for i in range(5):
        b.data[0][i] = 2
    assert minimax(b, depth=1, player=0) == -WIN_CONSTANT


def test_minimax_draw():
    b = Board(size=2, win_len=5)
    b.data[0] = [1, 2]
    b.data[1] = [2, 1]
    assert minimax(b, depth=1, player=0) == 0


def test_best_move_white():
    b = Board(size=7, win_len=5)
    b.place(0, 0)
    b.place(6, 0)
    b.place(0, 1)
    b.place(6, 1)
    b.place(0, 2)
    b.place(6, 2)
    b.place(0, 3)
    b.place(6, 3)
    assert get_best_move(b, player=0, depth=2) == (0, 4)


def test_best_move_black():
    b = Board(size=7, win_len=5)
    b.place(6, 0)
    b.place(0, 0)
    b.place(6, 1)
    b.place(0, 1)
    b.place(6, 2)
    b.place(0, 2)
    b.place(6, 3)
    b.place(0, 3)
    b.place(6, 4)
    assert get_best_move(b, player=1, depth=2) == (0, 4)


def test_best_move_outs_candidate_move():
    b = Board(size=5, win_len=5)
    b.place(2, 2)
    b.place(1, 2)
    move = get_best_move(b, player=0, depth=1)
    candidates = set(get_candidate_moves(b, distance=2))
    assert move in candidates

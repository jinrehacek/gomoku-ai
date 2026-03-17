import pytest
from gomoku.board import Board
import gomoku.engine as eng
from gomoku.engine import (
    get_candidate_moves,
    _immediate_neighbors,
    _candidate_distance,
    _move_wins_for,
    _order_moves_tactical,
    black_stones_eq,
    SearchState,
    check_time,
    eval_line,
    prepare_patterns,
    eval_board,
    minimax,
    get_best_move,
    iterative_deepening,
    COMPLETE_PATTERNS,
    OPENING_DISTANCE,
    MOVES_TO_CONSIDER_DIST,
    OPENING_MOVES_LIMIT,
    WIN_CONSTANT,
    WeAreSlow,
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


def test_get_candidate_moves_empty_history():
    b = Board(size=5, win_len=4)
    assert get_candidate_moves(b, 2) == [(2, 2)]


def test_black_stones_eq():
    assert black_stones_eq((0, 1, 2, 0, 1)) == (0, 2, 1, 0, 2)


def test_search_state_history():
    state = SearchState()
    assert state.get_history_score(0, (2, 2)) == 0

    state.update_history(0, (2, 2), depth=3)
    assert state.get_history_score(0, (2, 2)) == 9

    state.update_history(0, (2, 2), depth=2)
    assert state.get_history_score(0, (2, 2)) == 13


def test_check_time_raises():
    with pytest.raises(WeAreSlow):
        check_time(deadline=0.0, counter=[0])


def test_candidate_distance_opening_and_midgame():
    b = Board(size=7, win_len=5)
    assert _candidate_distance(b) == OPENING_DISTANCE

    for i in range(OPENING_MOVES_LIMIT):
        b.place(i % b.LENGTH, (i // b.LENGTH) % b.LENGTH)
    assert _candidate_distance(b) == MOVES_TO_CONSIDER_DIST


def test_move_wins_for_true_and_false():
    b = Board(size=7, win_len=5)
    b.data[0][0:4] = [1, 1, 1, 1]

    assert _move_wins_for(b, (0, 4), as_player=0)
    assert not _move_wins_for(b, (1, 1), as_player=0)


def test_order_moves_tactical_block_and_history_sort():
    b = Board(size=7, win_len=5)
    b.data[0][0:4] = [2, 2, 2, 2]
    moves = [(0, 4), (1, 1), (2, 2)]

    ordered = _order_moves_tactical(b, player=0, moves=moves)
    assert ordered == [(0, 4)]

    b2 = Board(size=7, win_len=5)
    state = SearchState()
    state.update_history(0, (3, 3), depth=4)
    state.update_history(0, (2, 2), depth=1)
    quiet_moves = [(1, 1), (2, 2), (3, 3)]

    ordered_quiet = _order_moves_tactical(b2, player=0, moves=quiet_moves, top_k=2, state=state)
    assert ordered_quiet[0] == (3, 3)
    assert len(ordered_quiet) == 2


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
    assert minimax(b, depth=1, player=1) == WIN_CONSTANT + 10


def test_minimax_black_wins():
    b = Board(size=7, win_len=5)
    for i in range(5):
        b.data[0][i] = 2
    assert minimax(b, depth=1, player=0) == -(WIN_CONSTANT + 10)


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


def test_minimax_updates_history():
    b = Board(size=5, win_len=4)
    b.place(2, 2)
    state = SearchState()

    minimax(
        b,
        depth=1,
        player=0,
        curr_eval=eval_board(b, COMPLETE_PATTERNS),
        alpha=0,
        beta=0,
        state=state,
    )
    assert len(state.history) >= 1


def test_get_best_move_with_pv_move():
    b = Board(size=5, win_len=5)
    b.place(2, 2)
    b.place(1, 2)

    candidates = get_candidate_moves(b, 2)
    pv = candidates[-1]
    move = get_best_move(b, player=0, depth=1, pv_move=pv)
    assert type(move) is tuple

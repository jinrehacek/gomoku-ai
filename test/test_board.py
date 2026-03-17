import pytest
from gomoku.board import Board, WHITE_STONE, BLACK_STONE, WHITE_TURN, BLACK_TURN

# WHITE/Black stone is 1 / 2 resp.
# White/Black turn is 0 / 1 resp. White starts

WHITE_WON, BLACK_WON, NO_WIN = WHITE_STONE, BLACK_STONE, 0
BOARD_FULL = 3
# we are testing for more "trivial" board 4x4 where 3 in row is winning - the mechanisms work identically


@pytest.fixture
def small_b43():
    return Board(size=4, win_len=3)


def test_creating():
    zero_arr = [[0 for _ in range(4)] for _ in range(4)]
    created = Board(size=4, win_len=3)
    assert created.data == zero_arr
    assert created.turn == WHITE_TURN
    assert created.LENGTH == 4
    assert created.WINNING_LENGTH == 3


def test_creating_default_values():
    created = Board()
    assert created.LENGTH == 15
    assert created.WINNING_LENGTH == 5
    assert created.turn == WHITE_TURN
    assert created.history == []


def test_place(small_b43):
    b = small_b43

    b.place(x=0, y=0)
    assert b.data[0][0] == WHITE_STONE

    b.place(2, 1)
    assert b.data[2][1] == BLACK_STONE  # because it changes the turn automatically

    b.place(1, 3)
    assert b.data[1][3] == WHITE_STONE
    assert b.history == [(0, 0), (2, 1), (1, 3)]


def test_place_turn(small_b43):
    b = small_b43
    assert b.turn == WHITE_TURN
    b.place(3, 3)
    assert b.turn == BLACK_TURN


def test_place_exception(small_b43):
    small_b43.place(2, 1)
    with pytest.raises(Exception) as exc:
        small_b43.place(2, 1)
    assert "already occupied" in str(exc.value)


def test_remove_stone(small_b43):
    with pytest.raises(Exception) as exc:
        small_b43.remove_stone(2, 1)
    assert "empty square" in str(exc.value)

    small_b43.place(2, 1)
    assert small_b43.data[2][1] == WHITE_STONE
    assert small_b43.turn == BLACK_TURN
    small_b43.remove_stone(2, 1)
    assert small_b43.data[2][1] == 0
    assert small_b43.turn == WHITE_TURN


def test_undo_move(small_b43):
    with pytest.raises(Exception) as exc:
        small_b43.undo_move()
    assert "No move has been played" in str(exc.value)

    small_b43.place(0, 0)
    small_b43.place(1, 1)

    # undo black move
    small_b43.undo_move()
    assert small_b43.data[1][1] == 0
    assert small_b43.turn == BLACK_TURN
    assert small_b43.history == [(0, 0)]

    # undo white move
    small_b43.undo_move()
    assert small_b43.data[0][0] == 0
    assert small_b43.turn == WHITE_TURN
    assert small_b43.history == []


def test_checkline(small_b43):
    assert small_b43.check_line([1, 1, 1, 1]) == NO_WIN
    assert small_b43.check_line([1, 1, 1, 0]) == WHITE_WON
    assert small_b43.check_line([0, 1, 1, 1]) == WHITE_WON
    assert small_b43.check_line([0, 2, 2, 2]) == BLACK_WON
    assert small_b43.check_line([0, 1, 2, 1]) == NO_WIN
    assert small_b43.check_line([0, 0, 0, 0]) == NO_WIN


def test_checkline2(small_b43):
    assert small_b43.check_line([1, 1, 0], IN_ROW=2) == WHITE_WON
    assert small_b43.check_line([2, 2, 1], IN_ROW=2) == BLACK_WON
    assert small_b43.check_line([1, 0, 1], IN_ROW=2) == NO_WIN


def test_is_full(small_b43):
    full_board = [[1 for _ in range(4)] for _ in range(4)]
    small_b43.data = full_board
    assert small_b43.is_full()

    b = Board(4, 3)
    assert not b.is_full()

    b.data = full_board
    b.data[3][2] = 0
    assert not b.is_full()

    b.place(3, 2)
    assert b.is_full()


def test_get_xy_row_col():
    b = Board(4, 3)
    b.data = [
        [1, 2, 0, 0],
        [0, 1, 2, 0],
        [2, 0, 1, 0],
        [0, 0, 0, 2],
    ]

    assert b._get_xy_row(1) == [0, 1, 2, 0]
    assert b._get_xy_col(2) == [0, 2, 1, 0]


def test_get_xy_diags():
    b = Board(4, 3)
    b.data = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16],
    ]

    assert b._get_xy_diag1(2, 1) == [5, 10, 15]
    assert b._get_xy_diag1(0, 3) == [4]
    assert b._get_xy_diag2(0, 2) == [9, 6, 3]
    assert b._get_xy_diag2(3, 3) == [16]


def test_get_all_diagonals_default_and_custom_min_len():
    b = Board(4, 3)
    b.data = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16],
    ]

    all_default = list(b._get_all_diagonals())
    assert len(all_default) == 7
    assert [13, 10, 7, 4] in all_default
    assert [1, 6, 11, 16] in all_default

    all_len4 = list(b._get_all_diagonals(min_pattern_len=4))
    assert len(all_len4) == 3
    assert [13, 10, 7, 4] in all_len4
    assert [1, 6, 11, 16] in all_len4


def test_get_all_lines_count_default_and_custom():
    b = Board(4, 3)
    all_default = list(b._get_all_lines())
    all_len4 = list(b._get_all_lines(min_pattern_len=4))

    # default: 4 cols + 4 rows + 7 diagonals
    assert len(all_default) == 15
    # min len 4: 4 cols + 4 rows + 3 diagonals
    assert len(all_len4) == 11


def test_is_over_row(small_b43):
    small_b43.data[0] = [1, 1, 1, 0]
    assert small_b43.is_over() == WHITE_WON


def test_is_over_col(small_b43):
    small_b43.data[0][1] = 2
    small_b43.data[1][1] = 2
    small_b43.data[2][1] = 2
    assert small_b43.is_over() == BLACK_WON


def test_is_over_diag_downhill(small_b43):
    small_b43.data[0][0] = 1
    small_b43.data[1][1] = 1
    small_b43.data[2][2] = 1
    assert small_b43.is_over() == WHITE_WON


def test_is_over_diag_uphill(small_b43):
    small_b43.data[0][2] = 2
    small_b43.data[1][1] = 2
    small_b43.data[2][0] = 2
    assert small_b43.is_over() == BLACK_WON

    b = Board(4, 3)
    b.data[3][1] = 1
    b.data[2][2] = 1
    b.data[1][3] = 1
    assert b.is_over() == WHITE_WON


def test_is_over_nobody(small_b43):
    small_b43.data[1] = [0, 1, 2, 2]
    assert small_b43.is_over() == NO_WIN


def test_is_over_draw(small_b43):
    small_b43.data = [
        [1, 1, 2, 2],
        [2, 2, 1, 1],
        [1, 1, 2, 2],
        [2, 2, 1, 1],
    ]
    assert small_b43.is_over() == BOARD_FULL


def test_is_over_with_history_row_win():
    b = Board(4, 3)
    b.place(0, 0)
    b.place(1, 0)
    b.place(0, 1)
    b.place(1, 1)
    b.place(0, 2)

    assert b.is_over() == WHITE_WON


def test_is_over_with_history_col_win():
    b = Board(4, 3)
    b.place(0, 0)
    b.place(0, 1)
    b.place(1, 0)
    b.place(1, 1)
    b.place(2, 0)

    assert b.is_over() == WHITE_WON


def test_is_over_with_history_diag1_win():
    b = Board(4, 3)
    b.place(0, 0)
    b.place(0, 1)
    b.place(1, 1)
    b.place(0, 2)
    b.place(2, 2)

    assert b.is_over() == WHITE_WON


def test_is_over_with_history_diag2_win():
    b = Board(4, 3)
    b.place(2, 0)
    b.place(0, 0)
    b.place(1, 1)
    b.place(0, 1)
    b.place(0, 2)

    assert b.is_over() == WHITE_WON


def test_is_over_with_history_nobody():
    b = Board(4, 3)
    b.place(0, 0)
    b.place(3, 3)
    b.place(0, 2)

    assert b.is_over() == NO_WIN


def test_is_over_with_history_draw():
    b = Board(2, 3)
    b.place(0, 0)
    b.place(0, 1)
    b.place(1, 0)
    b.place(1, 1)

    assert b.is_over() == BOARD_FULL

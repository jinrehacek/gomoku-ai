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


def test_place(small_b43):
    b = small_b43

    b.place(x=0, y=0)
    assert b.data[0][0] == WHITE_STONE

    b.place(2, 1)
    assert b.data[2][1] == BLACK_STONE  # because it changes the turn automatically

    b.place(1, 3)
    assert b.data[1][3] == WHITE_STONE


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


def test_checkline(small_b43):
    assert small_b43.check_line([1, 1, 1, 1]) == NO_WIN
    assert small_b43.check_line([1, 1, 1, 0]) == WHITE_WON
    assert small_b43.check_line([0, 1, 1, 1]) == WHITE_WON
    assert small_b43.check_line([0, 2, 2, 2]) == BLACK_WON
    assert small_b43.check_line([0, 1, 2, 1]) == NO_WIN
    assert small_b43.check_line([0, 0, 0, 0]) == NO_WIN


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

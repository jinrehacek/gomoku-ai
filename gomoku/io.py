import re
from typing import Literal

from gomoku.board import Board, Coord

# regex for validating coordinate format
validation_pattern = re.compile(r"^[A-Za-z]\d{1,2}$")


def valid_input(s: str) -> bool:
    """
    Validates board coordinate format like a5 or H12.
    """
    return bool(validation_pattern.fullmatch(s))


def board_coords_to_xy(s: str, board: Board) -> Coord | Literal[False]:
    """
    Converts board coordinate string to (x, y), validates bounds and occupancy.
    """
    if not valid_input(s):
        return False

    x = int(s[1:]) - 1
    y = ord(s[0].lower()) - ord("a")

    if x < 0 or y < 0:
        return False

    if x >= board.LENGTH or y >= board.LENGTH or board.data[x][y] != 0:
        return False

    return x, y


def xy_to_board_coords(x: int, y: int) -> str:
    """
    Converts internal board coordinates (x, y) to coordinate text like a1.
    """
    return f"{chr(ord('a') + y)}{x + 1}"

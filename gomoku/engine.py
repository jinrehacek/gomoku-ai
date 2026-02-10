# tady bude zit logika enginu ktery budu jenom importovat do nejspis IO.py
from gomoku.board import Board


def _immediate_neighbors(x, y, distance: int, board_size: int):
    VALS = range(-distance, distance + 1)  # apparently possible
    for i in VALS:
        for j in VALS:
            if i == j == 0:
                continue
            n_x, n_y = x + i, y + j
            if 0 <= n_x < board_size and 0 <= n_y < board_size:
                yield (n_x, n_y)


def get_candidate_moves(board: Board, distance: int) -> list[tuple[int, int]]:
    n = board.LENGTH
    # using sets for O(1) checking if coordinates are occupied or already in *out*
    # subject to change if candidate move order is needed
    occupied = set()
    out = set()
    for i in range(n):
        for j in range(n):
            if board.data[i][j] > 0:
                occupied.add((i, j))
    for x, y in occupied:
        for i, j in _immediate_neighbors(x, y, distance, n):
            if (i, j) not in out and (i, j) not in occupied:
                out.add((i, j))
    return list(out)

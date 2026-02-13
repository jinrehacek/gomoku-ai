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


SEARCH_PATTERNS = [
    (20, (2, 1, 1, 1, 0)),
    (75, (0, 1, 1, 1, 0)),
    (250, (2, 1, 1, 1, 1, 0)),
    (250, (1, 0, 1, 1, 1)),
    (250, (1, 1, 0, 1, 1)),
    (5000, (0, 1, 1, 1, 1, 0)),
]


def prepare_patterns(patterns):
    out: list[tuple[int, tuple[int]]] = []
    for pat in patterns:
        val, stones = pat
        rev = tuple([i for i in reversed(stones)])
        if stones == rev:
            out.append(pat)
        else:
            out.append(pat)
            out.append((val, rev))
    return out


# NOTE: do eval board nezapomenout dat min pattern legnth
# TEST: napsat pro tenhle shit testy
def eval_line(line: list[int], patterns: list[tuple[int, tuple[int]]], shortest_pat: int) -> int:
    """
    eval je z perspektivy bileho (+ kdyz vyhrav; - kdyz vyhrava cerny)
    """
    suma = 0
    for i in range(len(line) - shortest_pat + 1):
        for val, stones in patterns:
            len_pat = len(stones)

            # pokud by pattern presahnul line
            if i + len_pat > len(line):
                continue

            # napr pro i = 0 a len_pat = 4: 0 1 2 3
            window = tuple(line[i : i + len_pat])
            black_stones = tuple([(x % 2) + 1 if x else 0 for x in stones])

            if window == stones:
                suma += val
            elif window == black_stones:
                suma -= val
    return suma

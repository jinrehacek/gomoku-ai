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


def shortest_pattern(patterns: list[tuple[int, tuple]]) -> int:
    """
    returns int of length of shortest search pattern
    """
    lenghts = [len(x[1]) for x in patterns]
    return min(lenghts)


def prepare_patterns(patterns):
    """
    Adds mirror images of patterns and then all patterns from perspective of black player
    """
    out: list[tuple[int, tuple]] = []

    # Adding mirror images of patterns
    for pat in patterns:
        val, stones = pat
        rev = tuple([i for i in reversed(stones)])
        if stones == rev:
            out.append(pat)
        else:
            out.append(pat)
            out.append((val, rev))

    # Adding corresponding patterns for black with negative val
    for i in range(len(out)):
        val, stones = out[i]
        black_stones = tuple([(x % 2) + 1 if x else 0 for x in stones])
        out.append((-val, black_stones))

    return out


def eval_line(line: list[int], patterns: list[tuple[int, tuple]], shortest_pat: int) -> int:
    """
    eval je z perspektivy bileho (+ kdyz vyhrava; - kdyz vyhrava cerny)
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

            # pro patterns z pohledu cerneho je hodnota zaporna
            if window == stones:
                suma += val
    return suma


def eval_board(board: Board, patterns: list[tuple[int, tuple]], shortest_pat=None) -> int:
    if shortest_pat is None:
        shortest_pat = shortest_pattern(patterns)

    suma = 0
    for line in board._get_all_lines():
        suma += eval_line(line, patterns, shortest_pat)
    return suma


SHORTEST = shortest_pattern(SEARCH_PATTERNS)
COMPLETE_PATTERNS = prepare_patterns(SEARCH_PATTERNS)


def heuristic_eval(board: Board) -> int:
    return eval_board(board, COMPLETE_PATTERNS, SHORTEST)


WIN_CONSTANT = 99999999


def minimax(board: Board, depth: int, player: int) -> int | float:
    """
    MAX = 0, bily neb se zvysujici se eval_line vyhrava bily vice
    MIN = 1, cerny
    """
    if depth == 0:
        return heuristic_eval(board)

    situtation = board.is_over()
    if situtation > 0:
        a = situtation % 3
        a = -1 if a == 2 else a
        return a * WIN_CONSTANT  # mega velke cislo ktere prebije cokoliv jineho co je realen mozne dostat evaluaci herni plochy

    possible_moves = get_candidate_moves(board=board, distance=2)
    best_eval = float("inf") * (-1 if player == 0 else 1)

    for move in possible_moves:
        board.place(*move)
        evaluation = minimax(board, player=player ^ 1, depth=depth - 1)

        # cleanign the board
        board.remove_stone(*move)
        if player == 0:
            best_eval = max(best_eval, evaluation)
        else:
            best_eval = min(best_eval, evaluation)

    return best_eval


def get_best_move(board: Board, player: int, depth: int) -> tuple[int, int]:
    best_eval = float("inf") * (-1 if player == 0 else 1)
    possible_moves = get_candidate_moves(board=board, distance=2)
    best_move = None

    for move in possible_moves:
        board.place(*move)
        evaluation = minimax(board, player=player ^ 1, depth=depth - 1)

        board.remove_stone(*move)

        if player == 0:
            if evaluation > best_eval:
                best_eval, best_move = evaluation, move
        else:
            if evaluation < best_eval:
                best_eval, best_move = evaluation, move
    assert type(best_move) is tuple
    return best_move

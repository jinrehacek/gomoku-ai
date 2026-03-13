# tady bude zit logika enginu ktery budu jenom importovat do nejspis IO.py
from typing import Generator
from gomoku.board import Board, Coord
import time


SearchPatternsDict = dict[int, dict[tuple[int, ...], int]]


class WeAreSlow(Exception):
    pass


def _immediate_neighbors(x, y, distance: int, board_size: int) -> Generator[Coord]:
    """
    generates immediate neighbors of given square within some distance
    """
    VALS = range(-distance, distance + 1)  # apparently possible
    for i in VALS:
        for j in VALS:
            if i == j == 0:
                continue
            n_x, n_y = x + i, y + j
            if 0 <= n_x < board_size and 0 <= n_y < board_size:
                yield (n_x, n_y)


def get_candidate_moves(board: Board, distance: int) -> list[Coord]:
    """
    returns list of possible moves [Coord], sorted by proximity to last placed stone
    """
    n = board.LENGTH

    # using sets for O(1) checking if coordinates are occupied or already in *out*
    occupied = set()
    out = set()

    # NOTE: This should NEVER run
    if len(board.history) == 0:
        # WARNING: NENI HOTOVE - this should not happen as opening will be handled differently
        # but worst case this is usable
        return [(n // 2, n // 2)]

    # saves time cuz we have all placed stones here
    for x, y in board.history:
        occupied.add((x, y))

    for x, y in occupied:
        for i, j in _immediate_neighbors(x, y, distance, n):
            if (i, j) not in out and (i, j) not in occupied:
                out.add((i, j))

    unordered: list[Coord] = list(out)
    ordered: list[tuple[int, Coord]] = []

    # get the last placed stone
    lx, ly = board.history[-1]

    # Use inequality to sort by distance to last placed
    ordered = [(max(abs(lx - x), abs(ly - y)), (x, y)) for x, y in unordered]
    ordered.sort(key=lambda x: x[0])

    # cutout the distance "eval" and just output sorted moves
    out_moves: list[Coord] = [x[1] for x in ordered]
    return out_moves


SEARCH_PATTERNS = [
    (10, (2, 1, 1, 1, 2)),
    (20, (2, 1, 1, 1, 0)),
    (75, (0, 1, 1, 1, 0)),
    (250, (2, 1, 1, 1, 1, 0)),
    (250, (1, 0, 1, 1, 1)),
    (250, (1, 1, 0, 1, 1)),
    (5000, (0, 1, 1, 1, 1, 0)),
]


def prepare_patterns(patterns: list[tuple[int, tuple[int, ...]]]) -> SearchPatternsDict:
    """
    Adds mirror images of patterns and then all patterns from perspective of black player
    """

    # Dict{lenght of pattern: dict{pattern: score of pattern} }
    n_out: dict[int, dict[tuple[int, ...], int]] = {}

    # Adding mirror images of patterns
    for pat in patterns:
        val, stones = pat
        lgth = len(stones)
        n_out.setdefault(lgth, {})
        rev = tuple([i for i in reversed(stones)])
        if stones == rev:
            n_out[lgth][stones] = val

            black_stones = tuple([(x % 2) + 1 if x else 0 for x in stones])
            n_out[lgth][black_stones] = -val
        else:
            n_out[lgth][stones] = val
            n_out[lgth][rev] = val

            black_stones = tuple([(x % 2) + 1 if x else 0 for x in stones])
            n_out[lgth][black_stones] = -val

            black_rev = tuple([(x % 2) + 1 if x else 0 for x in rev])
            n_out[lgth][black_rev] = -val

    return n_out


def eval_line(line: list[int], patterns: SearchPatternsDict) -> int:
    """
    statically evalutaes given line - list[int] based on the given search patterns
    eval je z perspektivy bileho (+ kdyz vyhrava; - kdyz vyhrava cerny)
    """
    n = len(line)
    suma = 0

    # proseknujeme vsecchny patterns dle delky
    for lgth, posloupnosti in patterns.items():
        # patterny delsi nez line? nepotrebujeme
        if lgth > n:
            continue
        # nas pattern je kratsi? budeme posouvat n-lgth krat
        for i in range(0, n - lgth + 1):
            okno = tuple(line[i : i + lgth])
            score = posloupnosti.get(okno, 0)
            suma += score
    return suma


COMPLETE_PATTERNS: SearchPatternsDict = prepare_patterns(SEARCH_PATTERNS)
WIN_CONSTANT: int = 99999999
MOVES_TO_CONSIDER_DIST = 2


def eval_move(board: Board, x: int, y: int, patterns: SearchPatternsDict) -> int:
    d_row = eval_line(board._get_xy_row(x), patterns)
    d_col = eval_line(board._get_xy_col(y), patterns)
    d_diag1 = eval_line(board._get_xy_diag1(x, y), patterns)
    d_diag2 = eval_line(board._get_xy_diag2(x, y), patterns)
    suma = d_col + d_diag1 + d_diag2 + d_row
    return suma


# TEST: test new eval func


def eval_board(board: Board, patterns: SearchPatternsDict) -> int:
    suma = 0
    for line in board._get_all_lines():
        suma += eval_line(line, patterns)
    return suma


# TODO: vice vypocetniho caus do oblasti posledniho tahu - momentalne je prvni ta oblast... mozna dam i ten cas

# TODO: dalsi veci?


def check_time(deadline: float | None, counter: list[int] = [0]):
    if deadline is not None:
        counter[0] += 1
        if counter[0] % 256 == 1 and time.time() >= deadline:
            raise WeAreSlow


def minimax(
    board: Board,
    depth: int,
    player: int,
    curr_eval: int,
    alpha=float("-inf"),
    beta=float("+inf"),
    deadline: float | None = None,
    we_should_check: list[int] = [0],
) -> int | float:
    """
    MAX = 0, bily neb se zvysujici se eval_line vyhrava bily vice
    MIN = 1, cerny
    """

    # We look if the game isn't over
    situtation = board.is_over()
    if situtation > 0:
        a = situtation % 3
        a = -1 if a == 2 else a
        return a * WIN_CONSTANT  # mega velke cislo ktere prebije cokoliv jineho co je realen mozne dostat evaluaci herni plochy

    # if we reached final depth -> return static eval
    if depth == 0:
        return curr_eval

    check_time(deadline, we_should_check)

    possible_moves = get_candidate_moves(board=board, distance=MOVES_TO_CONSIDER_DIST)

    for move in possible_moves:
        # evaluating 4 affected lines by the new move
        before = eval_move(board, *move, COMPLETE_PATTERNS)
        board.place(*move)
        try:
            after = eval_move(board, *move, patterns=COMPLETE_PATTERNS)
            e_delta = after - before

            # recursion
            evaluation = minimax(
                board=board,
                player=player ^ 1,
                depth=depth - 1,
                curr_eval=curr_eval + e_delta,
                alpha=alpha,
                beta=beta,
                deadline=deadline,
                we_should_check=we_should_check,
            )
        finally:
            # undo move musi byt vzdy, i kdyz WeAreSlow
            board.undo_move()

        # what we found out
        if player == 0:
            # MAX
            alpha = max(alpha, evaluation)
            if alpha >= beta:  # MIN isn't dumb - won't go here -> no need to calculate -> break
                break
        else:
            # MIN
            beta = min(beta, evaluation)
            if beta <= alpha:  # MAX has better branch than this -> break
                break

    return alpha if player == 0 else beta


def get_best_move(
    board: Board,
    player: int,
    depth: int,
    we_should_check: list[int] = [0],  # protoze aby se presouvala reference, ne hodnota
    deadline: float | None = None,
) -> Coord:
    best_eval = float("inf") * (-1 if player == 0 else 1)
    possible_moves = get_candidate_moves(board=board, distance=MOVES_TO_CONSIDER_DIST)
    best_move = None

    our_alpha, our_beta = float("-inf"), float("+inf")

    base_eval = eval_board(board, COMPLETE_PATTERNS)

    for move in possible_moves:
        before = eval_move(board, *move, COMPLETE_PATTERNS)
        board.place(*move)
        try:
            after = eval_move(board, *move, patterns=COMPLETE_PATTERNS)
            e_delta = after - before
            # we dont pass alpha/beta cuz its the start, we have no values
            evaluation = minimax(
                board,
                player=player ^ 1,
                depth=depth - 1,
                curr_eval=base_eval + e_delta,
                alpha=our_alpha,
                beta=our_beta,
                deadline=deadline,
                we_should_check=we_should_check,
            )
        finally:
            board.undo_move()

        if player == 0:
            if evaluation > best_eval:
                best_eval, best_move = evaluation, move
            our_alpha = max(best_eval, our_alpha)
        else:
            if evaluation < best_eval:
                best_eval, best_move = evaluation, move
            our_beta = min(best_eval, our_beta)

    assert type(best_move) is tuple
    return best_move


def iterative_deepening(board: Board, player: int, given_time: int = 10) -> tuple[Coord, int]:
    """
    given_time: time to spend in SECONDS
    returns the best move found in the time
    """
    best_move = None
    start = time.time()
    deadline = start + given_time + 0.5
    depth = 0

    # TEST: HAVE TO TEST this shit
    while time.time() < deadline:
        depth += 1
        try:
            new_move = get_best_move(board, player, depth, deadline=deadline)
        except WeAreSlow:
            depth -= 1
            break
        best_move = new_move

    assert best_move is not None  # kvuli linteru
    return best_move, depth

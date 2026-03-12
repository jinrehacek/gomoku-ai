# tady bude zit logika enginu ktery budu jenom importovat do nejspis IO.py
from typing import Generator
from gomoku.board import Board, Coord
import time


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
    (20, (2, 1, 1, 1, 0)),
    (75, (0, 1, 1, 1, 0)),
    (250, (2, 1, 1, 1, 1, 0)),
    (250, (1, 0, 1, 1, 1)),
    (250, (1, 1, 0, 1, 1)),
    (5000, (0, 1, 1, 1, 1, 0)),
]


def shortest_pattern(patterns: list[tuple[int, tuple[int]]]) -> int:
    """
    returns int of length of shortest search pattern
    """
    lenghts = [len(x[1]) for x in patterns]
    return min(lenghts)


def prepare_patterns(patterns: list[tuple[int, tuple[int]]]):
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


SHORTEST: int = shortest_pattern(SEARCH_PATTERNS)
COMPLETE_PATTERNS = prepare_patterns(SEARCH_PATTERNS)
WIN_CONSTANT: int = 99999999
MOVES_TO_CONSIDER_DIST = 2


def eval_board(board: Board, patterns: list[tuple[int, tuple]], shortest_pat=None) -> int:
    if shortest_pat is None:
        shortest_pat = shortest_pattern(patterns)

    suma = 0
    for line in board._get_all_lines():
        suma += eval_line(line, patterns, shortest_pat)
    return suma


# TODO: vice vypocetniho caus do oblasti posledniho tahu - momentalne je prvni ta oblast... mozna dam i ten cas

# TODO: dalsi veci?


def minimax(board: Board, depth: int, player: int, alpha=float("-inf"), beta=float("+inf")) -> int | float:
    """
    MAX = 0, bily neb se zvysujici se eval_line vyhrava bily vice
    MIN = 1, cerny
    """

    situtation = board.is_over()
    if situtation > 0:
        a = situtation % 3
        a = -1 if a == 2 else a
        return a * WIN_CONSTANT  # mega velke cislo ktere prebije cokoliv jineho co je realen mozne dostat evaluaci herni plochy

    if depth == 0:
        return eval_board(board=board, patterns=COMPLETE_PATTERNS, shortest_pat=SHORTEST)

    possible_moves = get_candidate_moves(board=board, distance=MOVES_TO_CONSIDER_DIST)

    for move in possible_moves:
        board.place(*move)
        evaluation = minimax(board, player=player ^ 1, depth=depth - 1, alpha=alpha, beta=beta)

        # cleaning the board
        board.undo_move()

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


def get_best_move(board: Board, player: int, depth: int) -> Coord:
    best_eval = float("inf") * (-1 if player == 0 else 1)
    possible_moves = get_candidate_moves(board=board, distance=MOVES_TO_CONSIDER_DIST)
    best_move = None

    our_alpha, our_beta = float("-inf"), float("+inf")

    for move in possible_moves:
        board.place(*move)
        # we dont pass alpha/beta cuz its the start, we have no values
        evaluation = minimax(board, player=player ^ 1, depth=depth - 1, alpha=our_alpha, beta=our_beta)

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


def iterative_deepening(board: Board, player: int, given_time: int = 10) -> Coord:
    """
    given_time: time to spend in SECONDS
    returns the best move found in the time
    """
    best_move = None
    start = time.time()
    depth = 1

    # TEST: HAVE TO TEST this shit

    # TODO: if bored improve time handling - currenlty possible to go 2^n+1 fo depth we want - fucking cooked

    # absolutely laguhably sub-optimal - we dont have transposition table and hashing
    # edge case: start 0.001 s new massive depth -> disaster, OMG...
    while time.time() - start < given_time:
        new_move = get_best_move(board, player, depth)
        best_move = new_move
        depth += 1

    assert best_move is not None  # kvuli linteru
    return best_move

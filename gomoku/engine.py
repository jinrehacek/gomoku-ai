# tady bude zit logika enginu ktery budu jenom importovat do nejspis IO.py
import time
from typing import Generator

from gomoku.board import Board, Coord

SearchPatternsDict = dict[int, dict[tuple[int, ...], int]]

# History heuristic: key = (player, x, y), value = cumulative score
HistoryTable = dict[tuple[int, int, int], int]


class SearchState:
    """
    Holds mutable search state that gets bumped around in minimax
    handles history heuristic scores - we find move really cool before? big cutoff, it helped us? we try it AGAIN next ply or next iteration
    in deepening
    hold the counter of how many nodes/vertices we visited/played in self.counter
    """

    def __init__(self):
        self.counter: list[int] = [0]
        self.history: HistoryTable = {}

    def update_history(self, player: int, move: Coord, depth: int):
        """
        Award move that caused cutoff with bonus
        """
        key = (player, move[0], move[1])
        self.history[key] = self.history.get(key, 0) + depth * depth

    def get_history_score(self, player: int, move: Coord) -> int:
        """
        Get history score for move (0 if not seen before)
        """
        key = (player, move[0], move[1])
        return self.history.get(key, 0)


class WeAreSlow(Exception):
    """
    special exception only we know how to handle, if we raise it we let it bubble up the minimax to get_best_move up to
    iterative_deepening where we cathc it and send last fully calculated best_move out
    """

    pass


def _immediate_neighbors(x, y, distance: int, board_size: int) -> Generator[Coord]:
    """
    generates immediate neighbors of given square within some given distance
    """
    VALS = range(-distance, distance + 1)
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

    # just here as precaution, will never run
    if len(board.history) == 0:
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
    (120, (0, 1, 1, 0, 1, 0)),
    (120, (0, 1, 1, 0, 1, 2)),
    (120, (2, 1, 1, 0, 1, 0)),
    (250, (2, 1, 1, 1, 1, 0)),
    (250, (1, 0, 1, 1, 1)),
    (250, (1, 1, 0, 1, 1)),
    (5000, (0, 1, 1, 1, 1, 0)),
]


def black_stones_eq(pattern: tuple[int, ...]) -> tuple[int, ...]:
    """
    creates equivalent pattern from black POV
    just flips 1 with 2 in given pattern
    """
    return tuple([(x % 2) + 1 if x else 0 for x in pattern])


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
        # if length of the pattern not key in outer dict, create it
        n_out.setdefault(lgth, {})

        # reversed stone sequence
        rev = tuple([i for i in reversed(stones)])

        # the stone sequence is palindrome
        if stones == rev:
            n_out[lgth][stones] = val

            black_stones = black_stones_eq(stones)
            n_out[lgth][black_stones] = -val

        # the stone sequence ISN'T palindrome
        else:
            n_out[lgth][stones] = val
            n_out[lgth][rev] = val

            black_stones = black_stones_eq(stones)
            n_out[lgth][black_stones] = -val

            black_rev = black_stones_eq(rev)
            n_out[lgth][black_rev] = -val
    return n_out


def eval_line(line: list[int], patterns: SearchPatternsDict) -> int:
    """
    statically evaluates given line - list[int] based on the given search patterns
    eval is from the POV of WHITE (+ white is better; - black is better)
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


# patterns dict we use in other funcs
COMPLETE_PATTERNS: SearchPatternsDict = prepare_patterns(SEARCH_PATTERNS)

# IMPORTANT CONSTANTS
MOVES_TO_CONSIDER_DIST = 2  # normally we look for immediate neighbors distance = 2
OPENING_DISTANCE = 1  # in opening we only look for immediate neighbors distance = 1
OPENING_MOVES_LIMIT = 8  # after 8 or more stones are placed -> we arent in opening anymore
EVAL_MOVE_SLICE_HALF = 6  # how long is half of the slice in eval_move
TOP_K_MOVES = None  # was used before, kept in case the top k moves idea is revived
WIN_CONSTANT = 99999999  # eval constant if the position is won, just gigantic number
WHEN_TO_USE_TACTICS = float("inf")


def eval_move(board: Board, x: int, y: int, patterns: SearchPatternsDict) -> int:
    """
    very smart function, we only evaluate the change of board static eval caused by given move
    we look only at two diagonals, 1 row & 1 col - those whose part is the move we just played
    row & col is sliced so it just cares about slice big enough around such it fits every pattern
    """
    d_row = eval_line(board._get_xy_row(x)[max(0, y - EVAL_MOVE_SLICE_HALF) : y + EVAL_MOVE_SLICE_HALF + 1], patterns)
    d_col = eval_line(board._get_xy_col(y)[max(0, x - EVAL_MOVE_SLICE_HALF) : x + EVAL_MOVE_SLICE_HALF + 1], patterns)
    d_diag1 = eval_line(board._get_xy_diag1(x, y), patterns)
    d_diag2 = eval_line(board._get_xy_diag2(x, y), patterns)
    suma = d_col + d_diag1 + d_diag2 + d_row
    return suma


def eval_board(board: Board, patterns: SearchPatternsDict) -> int:
    """
    statically evaluates whole board using eval_line function
    """
    suma = 0
    for line in board._get_all_lines():
        suma += eval_line(line, patterns)
    return suma


def check_time(deadline: float | None, counter: list[int] | None = None):
    if deadline is not None and counter is not None:
        counter[0] += 1
        if counter[0] % 1024 == 1 and time.time() >= deadline:
            raise WeAreSlow


def _candidate_distance(board: Board) -> int:
    """
    in opening we keep search less moves, it shoudl be enough
    """
    if len(board.history) < OPENING_MOVES_LIMIT:
        return OPENING_DISTANCE
    return MOVES_TO_CONSIDER_DIST


def _move_wins_for(board: Board, move: Coord, as_player: int) -> bool:
    """
    True if as_player would win immediately by playing move now
    """
    original_turn = board.turn
    board.turn = as_player
    board.place(*move)
    try:
        we_want = as_player + 1
        return (
            board.check_line(board._get_xy_col(move[1])) == we_want
            or board.check_line(board._get_xy_row(move[0])) == we_want
            or board.check_line(board._get_xy_diag1(*move)) == we_want
            or board.check_line(board._get_xy_diag2(*move)) == we_want
        )
    finally:
        board.undo_move()
        board.turn = original_turn


def _order_moves_tactical(
    board: Board,
    player: int,
    moves: list[Coord],
    top_k: int | None = None,
    state: SearchState | None = None,
) -> list[Coord]:
    """
    Better move ordering for alpha-beta:
      1 immediate wins
      2 immediate blocks of opponents winning move
      3 remaining moves sorted by history heuristic (if available)
    """
    winning_moves: list[Coord] = []
    boring_moves: list[Coord] = []

    # is move immediate win? append to winning_moves and return just those, no need for other choices
    for move in moves:
        if _move_wins_for(board, move, player):
            winning_moves.append(move)
        else:
            boring_moves.append(move)

    if winning_moves:
        return winning_moves

    opponent = player ^ 1
    blocking_moves: list[Coord] = []
    boring_moves_no_blocks: list[Coord] = []

    # does the move block immediate win by opponent? same vibe as before
    opponent_winning_squares = {mv for mv in moves if _move_wins_for(board, mv, opponent)}
    for move in boring_moves:
        if move in opponent_winning_squares:
            blocking_moves.append(move)
        else:
            boring_moves_no_blocks.append(move)

    if blocking_moves:
        return blocking_moves

    # sort quiet moves by history heuristic if state is availiable
    if state is not None and state.history:
        boring_moves_no_blocks.sort(key=lambda m: state.get_history_score(player, m), reverse=True)

    # kept here just in case, not being used by the code rn
    if top_k is not None:
        return boring_moves_no_blocks[:top_k]

    return boring_moves_no_blocks


def minimax(
    board: Board,
    depth: int,
    player: int,
    curr_eval: int | None = None,
    alpha=float("-inf"),
    beta=float("+inf"),
    deadline: float | None = None,
    state: SearchState | None = None,
) -> int | float:
    """
    the main character
    depth: how many levels deep we should go in the subtree
    player: from whose perspective we are playing
    curr_eval: static evaluation of the board before we start trying moves
    alpha, beta: cutoff interval
    deadline: time till which we have to finish
    """

    # We look if the game isn't over
    situtation = board.is_over()
    if situtation > 0:
        a = situtation % 3
        a = -1 if a == 2 else a
        return a * (
            WIN_CONSTANT + (10 * depth)
        )  # mega velke cislo ktere prebije cokoliv jineho co je realen mozne dostat evaluaci herni plochy

    # if we didnt get curr_eval passed in (shouldnt happen), lets compute it and pass it down
    if curr_eval is None:
        curr_eval = eval_board(board, COMPLETE_PATTERNS)

    # if we reached final depth -> return static eval
    if depth == 0:
        return curr_eval

    # if we didnt get state passed in, initialize it and pass it down
    if state is None:
        state = SearchState()

    # if we are past deadline, please tell everyone WeAreSlow and kill us
    check_time(deadline, state.counter)

    possible_moves = get_candidate_moves(board=board, distance=_candidate_distance(board))

    # we apply the "advanced tactical ordering" ALWAYS
    if depth <= WHEN_TO_USE_TACTICS:
        possible_moves = _order_moves_tactical(
            board=board,
            player=player,
            moves=possible_moves,
            top_k=TOP_K_MOVES,
            state=state,
        )

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
                state=state,
            )
        finally:  # undo move musi byt vzdy, i kdyz WeAreSlow
            board.undo_move()

        # what we found out
        if player == 0:
            # MAX
            alpha = max(alpha, evaluation)
            if alpha >= beta:  # MIN isn't dumb - won't go here -> no need to calculate -> break
                state.update_history(player, move, depth)
                break
        else:
            # MIN
            beta = min(beta, evaluation)
            if beta <= alpha:  # MAX has better branch than this -> break
                state.update_history(player, move, depth)
                break

    return alpha if player == 0 else beta


def get_best_move(
    board: Board,
    player: int,
    depth: int,
    deadline: float | None = None,
    pv_move: Coord | None = None,
    state: SearchState | None = None,
) -> Coord:

    # if we didnt get state passed in, initialize it and pass it down
    if state is None:
        state = SearchState()

    # -inf | +inf for max | min
    best_eval = float("inf") * (-1 if player == 0 else 1)

    # get moves, order them by tactics aswell
    possible_moves = get_candidate_moves(board=board, distance=_candidate_distance(board))
    possible_moves = _order_moves_tactical(
        board=board,
        player=player,
        moves=possible_moves,
        state=state,
    )

    # if we got the best move from previous iteration of get_best_move,
    # then we will check it first thing
    if pv_move in possible_moves:
        possible_moves.pop(possible_moves.index(pv_move))
        possible_moves = [pv_move] + possible_moves

    best_move = None

    our_alpha, our_beta = float("-inf"), float("+inf")

    # eval of hte full board; to be passed into minimax
    base_eval = eval_board(board, COMPLETE_PATTERNS)

    for move in possible_moves:
        before = eval_move(board, *move, COMPLETE_PATTERNS)
        board.place(*move)
        # try/finnally bcs of WeAreSlow
        # no expect bcs we want ti to bubbe up to iterative_deepening
        try:
            # how does the move change the board eval
            after = eval_move(board, *move, patterns=COMPLETE_PATTERNS)
            e_delta = after - before

            evaluation = minimax(
                board,
                player=player ^ 1,
                depth=depth - 1,
                curr_eval=base_eval + e_delta,
                alpha=our_alpha,
                beta=our_beta,
                deadline=deadline,
                state=state,
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

    # shared state across all iterations -> history heuristic gets bigger/better
    state = SearchState()

    while time.time() < deadline:
        depth += 1
        try:
            if best_move is not None:
                new_move = get_best_move(board, player, depth, deadline=deadline, pv_move=best_move, state=state)
            else:
                new_move = get_best_move(board, player, depth, deadline=deadline, state=state)
        except WeAreSlow:
            depth -= 1
            break
        best_move = new_move

    assert best_move is not None  # kvuli linteru
    return best_move, depth

# tady bude zit logika enginu ktery budu jenom importovat do nejspis IO.py
import random
import time
from dataclasses import dataclass
from typing import Generator, Literal

from gomoku.board import Board, Coord

SearchPatternsDict = dict[int, dict[tuple[int, ...], int]]

# History heuristic: key = (player, x, y), value = cumulative score
HistoryTable = dict[tuple[int, int, int], int]

TTFlag = Literal["exact", "lower", "upper"]


@dataclass(slots=True)
class TTEntry:
    depth: int
    value: int | float
    flag: TTFlag
    best_move: Coord | None = None


TranspositionTable = dict[int, TTEntry]


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
        self.tt: TranspositionTable = {}
        self.killers: dict[int, list[Coord]] = {}

    def start_new_search(self):
        self.counter[0] = 0

        # Age history so older cutoffs do not dominate forever.
        if self.history:
            aged: HistoryTable = {}
            for key, score in self.history.items():
                n_score = score // 2
                if n_score > 0:
                    aged[key] = n_score
            self.history = aged

        self.killers.clear()

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

    def update_killer(self, ply: int, move: Coord):
        row = self.killers.setdefault(ply, [])
        if move in row:
            row.remove(move)
            row.insert(0, move)
            return
        row.insert(0, move)
        if len(row) > 2:
            row.pop()

    def killer_bonus(self, ply: int, move: Coord) -> int:
        row = self.killers.get(ply)
        if not row:
            return 0
        if row and move == row[0]:
            return 2_000_000_000
        if len(row) > 1 and move == row[1]:
            return 1_000_000_000
        return 0


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
    if not board.history:
        return [(n // 2, n // 2)]

    out = set()
    data = board.data

    for x, y in board.history:
        min_x = x - distance if x - distance > 0 else 0
        max_x = x + distance if x + distance < n - 1 else n - 1
        min_y = y - distance if y - distance > 0 else 0
        max_y = y + distance if y + distance < n - 1 else n - 1

        for i in range(min_x, max_x + 1):
            for j in range(min_y, max_y + 1):
                if data[i][j] == 0:
                    out.add((i, j))

    lx, ly = board.history[-1]
    return sorted(list(out), key=lambda p: max(abs(lx - p[0]), abs(ly - p[1])))


SEARCH_PATTERNS = [
    # 2s
    (10, (0, 1, 1, 0, 0)),
    (10, (0, 0, 1, 1, 0)),
    (10, (0, 1, 0, 1, 0)),
    # 3s
    (20, (2, 1, 1, 1, 0, 0)),
    (20, (0, 0, 1, 1, 1, 2)),
    (75, (0, 1, 1, 1, 0)),
    (75, (0, 1, 0, 1, 1, 0)),
    (75, (0, 1, 1, 0, 1, 0)),
    # 4s
    (250, (2, 1, 1, 1, 1, 0)),
    (250, (0, 1, 1, 1, 1, 2)),
    (250, (2, 1, 1, 1, 0, 1, 2)),
    (250, (2, 1, 1, 0, 1, 1, 2)),
    (250, (2, 1, 0, 1, 1, 1, 2)),
    (250, (1, 0, 1, 1, 1)),
    (250, (1, 1, 0, 1, 1)),
    (250, (1, 1, 1, 0, 1)),
    (5000, (0, 1, 1, 1, 1, 0)),
    (5000, (0, 1, 1, 1, 0, 1, 0)),
    (5000, (0, 1, 1, 0, 1, 1, 0)),
    (5000, (0, 1, 0, 1, 1, 1, 0)),
    (999999, (1, 1, 1, 1, 1)),
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
    if n == 0:
        return 0
    suma = 0

    # proseknujeme vsecchny patterns dle delky
    for lgth, posloupnosti in patterns.items():
        # patterny delsi nez line? nepotrebujeme
        if lgth > n:
            continue
        get_score = posloupnosti.get
        # nas pattern je kratsi? budeme posouvat n-lgth krat
        for i in range(0, n - lgth + 1):
            score = get_score(tuple(line[i : i + lgth]), 0)
            if score:
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
WHEN_TO_USE_TACTICS = 3
MAX_TT_SIZE = 500_000
ASPIRATION_BASE = 200
TACTICS_MAX_PLY = 2


def _move_cap(depth: int, ply: int, count: int) -> int:
    if count <= 1:
        return count
    if depth >= 8:
        return min(count, 48)
    if depth >= 7:
        return min(count, 56)
    if depth >= 6:
        return min(count, 72)
    if depth >= 5 and ply >= 2:
        return min(count, 96)
    return count


def _order_moves_fast(player: int, moves: list[Coord], state: SearchState | None, ply: int) -> list[Coord]:
    if state is None:
        return moves
    return sorted(
        moves,
        key=lambda m: state.get_history_score(player, m) + state.killer_bonus(ply, m),
        reverse=True,
    )


# Zobrist hashing tables by board size
_ZOBRIST_TABLES: dict[int, list[list[tuple[int, int, int]]]] = {}
_ZOBRIST_TURN_KEY: dict[int, int] = {}


def _get_zobrist_table(size: int) -> tuple[list[list[tuple[int, int, int]]], int]:
    table = _ZOBRIST_TABLES.get(size)
    turn_key = _ZOBRIST_TURN_KEY.get(size)
    if table is not None and turn_key is not None:
        return table, turn_key

    rng = random.Random(0xC0FFEE + size)
    table = [
        [
            (
                0,
                rng.getrandbits(64),
                rng.getrandbits(64),
            )
            for _ in range(size)
        ]
        for _ in range(size)
    ]
    turn_key = rng.getrandbits(64)

    _ZOBRIST_TABLES[size] = table
    _ZOBRIST_TURN_KEY[size] = turn_key
    return table, turn_key


def _zobrist_hash(board: Board, player: int) -> int:
    table, turn_key = _get_zobrist_table(board.LENGTH)
    h = 0
    for x in range(board.LENGTH):
        for y in range(board.LENGTH):
            stone = board.data[x][y]
            if stone:
                h ^= table[x][y][stone]
    if player == 1:
        h ^= turn_key
    return h


def _tt_lookup(
    tt: TranspositionTable,
    key: int,
    depth: int,
    alpha: float | int,
    beta: float | int,
) -> tuple[int | float | None, float | int, float | int, Coord | None]:
    entry = tt.get(key)
    if entry is None:
        return None, alpha, beta, None

    if entry.depth < depth:
        return None, alpha, beta, entry.best_move

    if entry.flag == "exact":
        return entry.value, alpha, beta, entry.best_move

    if entry.flag == "lower":
        alpha = max(alpha, entry.value)
    elif entry.flag == "upper":
        beta = min(beta, entry.value)

    if alpha >= beta:
        return entry.value, alpha, beta, entry.best_move

    return None, alpha, beta, entry.best_move


def _tt_store(
    tt: TranspositionTable,
    key: int,
    depth: int,
    value: int | float,
    alpha_orig: float | int,
    beta_orig: float | int,
    best_move: Coord | None,
):
    if value <= alpha_orig:
        flag: TTFlag = "upper"
    elif value >= beta_orig:
        flag = "lower"
    else:
        flag = "exact"

    prev = tt.get(key)
    if prev is None or depth >= prev.depth:
        tt[key] = TTEntry(depth=depth, value=value, flag=flag, best_move=best_move)

    if len(tt) > MAX_TT_SIZE:
        tt.clear()


def eval_move(board: Board, x: int, y: int, patterns: SearchPatternsDict) -> int:
    """
    very smart function, we only evaluate the change of board static eval caused by given move
    we look only at two diagonals, 1 row & 1 col - those whose part is the move we just played
    row & col is sliced so it just cares about slice big enough around such it fits every pattern
    """
    half = EVAL_MOVE_SLICE_HALF
    size = board.LENGTH
    data = board.data

    # Fix: slice row around y, col around x
    row_slice = data[x][max(0, y - half) : min(size, y + half + 1)]
    col_slice = [data[i][y] for i in range(max(0, x - half), min(size, x + half + 1))]
    
    # Opt: slice diagonals too
    diag1_slice = []
    start_i = max(-half, -x, -y)
    end_i = min(half, size - 1 - x, size - 1 - y)
    for i in range(start_i, end_i + 1):
        diag1_slice.append(data[x + i][y + i])
        
    diag2_slice = []
    start_i = max(-half, -x, y - size + 1)
    end_i = min(half, size - 1 - x, y)
    for i in range(start_i, end_i + 1):
        diag2_slice.append(data[x + i][y - i])
        
    d_row = eval_line(row_slice, patterns)
    d_col = eval_line(col_slice, patterns)
    d_diag1 = eval_line(diag1_slice, patterns)
    d_diag2 = eval_line(diag2_slice, patterns)
    
    return d_row + d_col + d_diag1 + d_diag2


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
    r, c = move
    stone = as_player + 1
    data = board.data
    size = board.LENGTH

    # Horizontal
    count = 1
    for i in range(1, 5):
        if c + i < size and data[r][c + i] == stone: count += 1
        else: break
    for i in range(1, 5):
        if c - i >= 0 and data[r][c - i] == stone: count += 1
        else: break
    if count >= 5: return True

    # Vertical
    count = 1
    for i in range(1, 5):
        if r + i < size and data[r + i][c] == stone: count += 1
        else: break
    for i in range(1, 5):
        if r - i >= 0 and data[r - i][c] == stone: count += 1
        else: break
    if count >= 5: return True

    # Diagonal \
    count = 1
    for i in range(1, 5):
        if r + i < size and c + i < size and data[r + i][c + i] == stone: count += 1
        else: break
    for i in range(1, 5):
        if r - i >= 0 and c - i >= 0 and data[r - i][c - i] == stone: count += 1
        else: break
    if count >= 5: return True

    # Diagonal /
    count = 1
    for i in range(1, 5):
        if r + i < size and c - i >= 0 and data[r + i][c - i] == stone: count += 1
        else: break
    for i in range(1, 5):
        if r - i >= 0 and c + i < size and data[r - i][c + i] == stone: count += 1
        else: break
    if count >= 5: return True

    return False


def _order_moves_tactical(
    board: Board,
    player: int,
    moves: list[Coord],
    top_k: int | None = None,
    state: SearchState | None = None,
    ply: int = 0,
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
    if state is not None:
        boring_moves_no_blocks.sort(
            key=lambda m: state.get_history_score(player, m) + state.killer_bonus(ply, m),
            reverse=True,
        )

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
    zobrist_key: int | None = None,
    ply: int = 0,
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

    if zobrist_key is None:
        zobrist_key = _zobrist_hash(board, player)

    # if we are past deadline, please tell everyone WeAreSlow and kill us
    check_time(deadline, state.counter)

    alpha_orig, beta_orig = alpha, beta
    tt_hit, alpha, beta, tt_best_move = _tt_lookup(state.tt, zobrist_key, depth, alpha, beta)
    if tt_hit is not None:
        return tt_hit

    possible_moves = get_candidate_moves(board=board, distance=_candidate_distance(board))

    # Tactical ordering is expensive; use it near root / shallow search.
    if depth <= WHEN_TO_USE_TACTICS or ply <= TACTICS_MAX_PLY:
        possible_moves = _order_moves_tactical(
            board=board,
            player=player,
            moves=possible_moves,
            top_k=TOP_K_MOVES,
            state=state,
            ply=ply,
        )
    else:
        possible_moves = _order_moves_fast(player, possible_moves, state, ply)

    if tt_best_move in possible_moves:
        possible_moves.pop(possible_moves.index(tt_best_move))
        possible_moves = [tt_best_move] + possible_moves

    cap = _move_cap(depth, ply, len(possible_moves))
    if cap < len(possible_moves):
        possible_moves = possible_moves[:cap]

    best_move: Coord | None = None
    table, turn_key = _get_zobrist_table(board.LENGTH)
    is_first = True

    for move_idx, move in enumerate(possible_moves):
        # evaluating 4 affected lines by the new move
        before = eval_move(board, *move, COMPLETE_PATTERNS)

        stone = board.turn + 1
        child_key = zobrist_key ^ table[move[0]][move[1]][stone] ^ turn_key

        board.place(*move)
        try:
            after = eval_move(board, *move, patterns=COMPLETE_PATTERNS)
            e_delta = after - before

            next_eval = curr_eval + e_delta

            reduction = 0
            if depth >= 3 and not is_first and ply > 0:
                if move_idx >= 4:
                    reduction = 1
                    if move_idx >= 12 and depth >= 4:
                        reduction = 2

            # PVS: full window for first move, null-window for later moves.
            if is_first:
                evaluation = minimax(
                    board=board,
                    player=player ^ 1,
                    depth=depth - 1,
                    curr_eval=next_eval,
                    alpha=alpha,
                    beta=beta,
                    deadline=deadline,
                    state=state,
                    zobrist_key=child_key,
                    ply=ply + 1,
                )
            elif player == 0:
                if reduction > 0:
                    evaluation = minimax(
                        board=board,
                        player=player ^ 1,
                        depth=depth - 1 - reduction,
                        curr_eval=next_eval,
                        alpha=alpha,
                        beta=alpha + 1,
                        deadline=deadline,
                        state=state,
                        zobrist_key=child_key,
                        ply=ply + 1,
                    )
                    if evaluation > alpha:
                        reduction = 0

                if reduction == 0:
                    evaluation = minimax(
                        board=board,
                        player=player ^ 1,
                        depth=depth - 1,
                        curr_eval=next_eval,
                        alpha=alpha,
                        beta=alpha + 1,
                        deadline=deadline,
                        state=state,
                        zobrist_key=child_key,
                        ply=ply + 1,
                    )
                    if alpha < evaluation < beta:
                        evaluation = minimax(
                            board=board,
                            player=player ^ 1,
                            depth=depth - 1,
                            curr_eval=next_eval,
                            alpha=alpha,
                            beta=beta,
                            deadline=deadline,
                            state=state,
                            zobrist_key=child_key,
                            ply=ply + 1,
                        )
            else:
                if reduction > 0:
                    evaluation = minimax(
                        board=board,
                        player=player ^ 1,
                        depth=depth - 1 - reduction,
                        curr_eval=next_eval,
                        alpha=beta - 1,
                        beta=beta,
                        deadline=deadline,
                        state=state,
                        zobrist_key=child_key,
                        ply=ply + 1,
                    )
                    if evaluation < beta:
                        reduction = 0

                if reduction == 0:
                    evaluation = minimax(
                        board=board,
                        player=player ^ 1,
                        depth=depth - 1,
                        curr_eval=next_eval,
                        alpha=beta - 1,
                        beta=beta,
                        deadline=deadline,
                        state=state,
                        zobrist_key=child_key,
                        ply=ply + 1,
                    )
                    if alpha < evaluation < beta:
                        evaluation = minimax(
                            board=board,
                            player=player ^ 1,
                            depth=depth - 1,
                            curr_eval=next_eval,
                            alpha=alpha,
                            beta=beta,
                            deadline=deadline,
                            state=state,
                            zobrist_key=child_key,
                            ply=ply + 1,
                        )
        finally:  # undo move musi byt vzdy, i kdyz WeAreSlow
            board.undo_move()
        is_first = False

        # what we found out
        if player == 0:
            # MAX
            if evaluation > alpha:
                alpha = evaluation
                best_move = move
            if alpha >= beta:  # MIN isn't dumb - won't go here -> no need to calculate -> break
                state.update_history(player, move, depth)
                state.update_killer(ply, move)
                best_move = move
                break
        else:
            # MIN
            if evaluation < beta:
                beta = evaluation
                best_move = move
            if beta <= alpha:  # MAX has better branch than this -> break
                state.update_history(player, move, depth)
                state.update_killer(ply, move)
                best_move = move
                break

    node_value = alpha if player == 0 else beta
    _tt_store(state.tt, zobrist_key, depth, node_value, alpha_orig, beta_orig, best_move)
    return node_value


def _search_root(
    board: Board,
    player: int,
    depth: int,
    deadline: float | None = None,
    pv_move: Coord | None = None,
    state: SearchState | None = None,
    alpha: float | int = float("-inf"),
    beta: float | int = float("+inf"),
    skip_state_reset: bool = False,
) -> tuple[Coord, int | float]:
    # if we didnt get state passed in, initialize it and pass it down
    if state is None:
        state = SearchState()

    if not skip_state_reset:
        state.start_new_search()

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

    our_alpha, our_beta = alpha, beta
    alpha_orig, beta_orig = our_alpha, our_beta

    root_key = _zobrist_hash(board, player)
    tt_entry = state.tt.get(root_key)
    tt_move = tt_entry.best_move if tt_entry is not None else None

    # eval of hte full board; to be passed into minimax
    base_eval = eval_board(board, COMPLETE_PATTERNS)

    # keep TT move near front if available
    if tt_move in possible_moves and tt_move != possible_moves[0]:
        possible_moves.pop(possible_moves.index(tt_move))
        possible_moves = [tt_move] + possible_moves

    table, turn_key = _get_zobrist_table(board.LENGTH)

    for move in possible_moves:
        before = eval_move(board, *move, COMPLETE_PATTERNS)

        stone = board.turn + 1
        child_key = root_key ^ table[move[0]][move[1]][stone] ^ turn_key

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
                zobrist_key=child_key,
                ply=1,
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
    _tt_store(state.tt, root_key, depth, best_eval, alpha_orig, beta_orig, best_move)
    return best_move, best_eval


def get_best_move(
    board: Board,
    player: int,
    depth: int,
    deadline: float | None = None,
    pv_move: Coord | None = None,
    state: SearchState | None = None,
    alpha: float | int = float("-inf"),
    beta: float | int = float("+inf"),
    skip_state_reset: bool = False,
) -> Coord:
    best_move, _ = _search_root(
        board=board,
        player=player,
        depth=depth,
        deadline=deadline,
        pv_move=pv_move,
        state=state,
        alpha=alpha,
        beta=beta,
        skip_state_reset=skip_state_reset,
    )
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
    prev_eval: int | float | None = None

    while time.time() < deadline:
        depth += 1
        try:
            state.start_new_search()

            width = ASPIRATION_BASE + depth * 80
            if prev_eval is None:
                a, b = float("-inf"), float("+inf")
            else:
                a, b = prev_eval - width, prev_eval + width

            if best_move is not None:
                new_move, new_eval = _search_root(
                    board,
                    player,
                    depth,
                    deadline=deadline,
                    pv_move=best_move,
                    state=state,
                    alpha=a,
                    beta=b,
                    skip_state_reset=True,
                )
            else:
                new_move, new_eval = _search_root(
                    board,
                    player,
                    depth,
                    deadline=deadline,
                    state=state,
                    alpha=a,
                    beta=b,
                    skip_state_reset=True,
                )

            # If aspiration failed low/high, retry full window at same depth.
            if new_eval <= a or new_eval >= b:
                new_move, new_eval = _search_root(
                    board,
                    player,
                    depth=depth,
                    deadline=deadline,
                    pv_move=new_move,
                    state=state,
                    alpha=float("-inf"),
                    beta=float("+inf"),
                    skip_state_reset=True,
                )

            prev_eval = new_eval
        except WeAreSlow:
            depth -= 1
            break
        best_move = new_move

    assert best_move is not None  # kvuli linteru
    return best_move, depth

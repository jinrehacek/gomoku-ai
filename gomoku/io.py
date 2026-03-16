# MY RICH IMPORTS
from typing import Literal, cast
from rich.text import Text
from rich.console import Console
from rich.table import Table
from rich.box import MINIMAL as TABLE_STYLE
from rich.prompt import Prompt

# GOMOKU imports
from gomoku.board import Board, Coord, Player
from gomoku.engine import COMPLETE_PATTERNS, eval_board, iterative_deepening, get_best_move, minimax

import time
import re
from random import randint

# the main hero, bridges stdout with whatever shit i have
cons = Console()


def create_table(board: Board) -> Table:
    size = board.LENGTH
    grid = Table(show_header=False, show_edge=False, show_lines=True, box=TABLE_STYLE)

    # MAPUJE JAK SE ZOBRAZI KAMENY
    mapa = {0: Text(""), 1: Text("X", style="bold red"), 2: Text("O", style="bold blue")}

    pismenka = [chr(ord("a") + x) for x in range(size)]
    numbers = [str(x) for x in range(1, size + 1)]
    for i in range(size + 1):
        if i == 0:
            grid.add_column(justify="right", width=2)
        else:
            grid.add_column(justify="center", width=1)

    # add rows one by one
    grid.add_row(Text(" "), *pismenka)
    for i in range(0, size):
        row = board.data[i]
        new_row = [mapa[x] for x in row]
        grid.add_row(Text(numbers[i], style=""), *new_row)

    # STYLING ROW a COL kde polozen posledni kamen
    LAST_PLACED_STYLE = "orange_red1"

    if len(board.history) > 0:
        l_x, l_y = board.history[-1]
        grid.rows[l_x + 1].style = LAST_PLACED_STYLE
        grid.columns[l_y + 1].style = LAST_PLACED_STYLE

    return grid


validation_pattern = re.compile(r"^[A-Za-z]\d{1,2}$")


def valid_input(s: str) -> bool:
    return bool(validation_pattern.fullmatch(s))


def board_coords_to_xy(s: str, board: Board) -> Coord | Literal[False]:
    if not valid_input(s):
        return False

    x = int(s[1:]) - 1
    y = ord(s[0].lower()) - ord("a")

    if x < 0 or y < 0:
        return False

    if x >= board.LENGTH or y >= board.LENGTH or board.data[x][y] != 0:
        return False

    return x, y


def redraw_board(board: Board):
    cons.clear()
    board_table = create_table(board)
    cons.print(board_table)


def get_inp_num(message: str, ok_nums: list[int]):
    while True:
        s = Prompt.ask(Text(message))
        num = int(s.strip())
        if num in ok_nums:
            return num
        else:
            cons.print("[orange_red1] Wrong input, please try again.")


def pick_mode_and_swap() -> tuple[int, int]:
    """
    returns (mode of the game, who starts swap)
    mode: 1 = human vs AI, 2 = AI vs AI
    swap: 1 = human sets it up, 2 = AI does
    """
    cons.print(Text("Do you want to play Human vs AI (1), or watch matchup AI vs. AI? (2)"))
    mode = get_inp_num("Input 1 or 2 accordingly", [1, 2])

    if mode == 1:
        cons.print(Text("Who do you want to start/set-up Swap-2? \n(1) You\n(2) AI\n(3) Suprise me."))
        swap = get_inp_num("Input number of your choice", [1, 2, 3])
        if swap == 3:
            swap = randint(1, 2)
        return 1, swap
    return 2, 0


def computer_chooses_side(board: Board, time_limit: int, fixed: int) -> Player:
    current_player = cast(Player, board.turn)
    opening_eval = minimax(board, 4, current_player, curr_eval=eval_board(board, COMPLETE_PATTERNS))

    if opening_eval > 0:
        ai_player = cast(Player, 0)
    elif opening_eval <= 0:
        ai_player = cast(Player, 1)
    else:
        ai_player = current_player

    human_player = cast(Player, ai_player ^ 1)

    if ai_player == current_player:
        cons.print("Computer chose the side to move now.")
        ai_move(board, time_limit=time_limit, fixed=fixed)
    else:
        cons.print("Computer chose the other side. Please make a move.")

    return human_player


def human_swap(board: Board, time_limit: int, fixed: int) -> Player:
    while True:
        a = Prompt.ask(
            Text(
                "Please input the coordinations of Swap2 opening in format 'cross_1 cross_2 circle_1' \n eg. 'a1 h5 b2' where cross stones are on a1 and h5"
            )
        )
        coords = a.strip().split()
        if len(coords) != 3:
            cons.print("[orange_red1]Please input exactly 3 coordinates.[/orange_red1]")
            continue

        c = tuple([board_coords_to_xy(x, board) for x in coords])
        if False in c:
            cons.print("[orange_red1]Wrong input or occupied square. Please try again.")
            continue
        else:
            b1, b2, w1 = c
            break

    board.place(*b1)  # pyright: ignore
    board.place(*w1)  # pyright: ignore
    board.place(*b2)  # pyright: ignore
    redraw_board(board)

    return computer_chooses_side(board, time_limit, fixed)


def ai_swap(board: Board, time_limit: int, fixed: int) -> Player:
    lght = board.LENGTH
    half = lght // 4
    board.place(half, half)
    board.place(lght // 2 + randint(-half, half), lght // 2)
    board.place(lght - half, lght - half + randint(-half, half))
    redraw_board(board)

    cons.print(Text("Do you want to play this position as (1) cross/X, (2) circle/O or (3) add two more stones?"))
    swap = get_inp_num("Input number of your choice", [1, 2, 3])
    current_player = cast(Player, board.turn)
    if swap == 2:
        return current_player

    if swap == 1:
        human_player = cast(Player, current_player ^ 1)
        ai_move(board, time_limit=time_limit, fixed=fixed)
        return human_player

    # If player chooses to add 2 more stones
    while True:
        a = Prompt.ask(
            Text(
                "Please input the coordinations of the additional stones in format 'cross_1 circle_1' \n eg. 'a1 b2' where cross is on a1"
            )
        )
        coords = a.strip().split()
        if len(coords) != 2:
            cons.print("[orange_red1]Please input exactly 2 coordinates.[/orange_red1]")
            continue

        c = tuple([board_coords_to_xy(x, board) for x in coords])
        if False in c:
            cons.print("[orange_red1]Wrong input or occupied square. Please try again.")
            continue
        else:
            b1, w1 = c
            break

    board.place(*b1)  # pyright: ignore
    board.place(*w1)  # pyright: ignore
    redraw_board(board)

    return computer_chooses_side(board, time_limit, fixed)


def ai_vs_ai_swap(board: Board, time_limit: int, fixed: int):
    lght = board.LENGTH
    half = lght // 4
    board.place(half, half)
    board.place(lght // 2 + randint(-half, half), lght // 2)
    board.place(lght - half, lght - half + randint(-half, half))
    redraw_board(board)

    current_player = cast(Player, board.turn)
    opening_eval = minimax(board, 4, current_player, curr_eval=eval_board(board, COMPLETE_PATTERNS))

    if opening_eval > 0:
        ai_player = cast(Player, 0)
    elif opening_eval <= 0:
        ai_player = cast(Player, 1)
    else:
        ai_player = current_player

    if ai_player == current_player:
        cons.print("Second AI chose the side to move now.")
    else:
        cons.print("Second AI chose the other side.")
        ai_move(board, time_limit=time_limit, fixed=fixed)


def human_move(board: Board):
    checked: Coord | bool = False
    while True:
        user_move = Prompt.ask("Enter your move (g8, a5, ...)")
        checked = board_coords_to_xy(user_move, board)
        if checked is not False:
            break
        cons.print("[orange_red1]Wrong input or occupied square. Please try again.")

    board.place(*checked)
    redraw_board(board)


def ai_move(board: Board, time_limit: int, fixed: int, as_player: Player | None = None):
    # COMPLET SEARCH PATTERNS jsou computed on IMPORT, tedy jen JEDNOU
    cons.print("[magenta] AI is deep in thought.")

    start = time.time()

    if as_player is None:
        as_player = cast(Player, board.turn)

    if fixed == 0:
        ai_move, depth = iterative_deepening(board, as_player, time_limit)  # board, player, given_time
    else:
        ai_move = get_best_move(board, as_player, fixed)
        depth = fixed
    board.place(*ai_move)

    redraw_board(board)

    cons.print("AI pondered for " + str(round(time.time() - start, 2)) + " seconds. (Beep boop)")
    cons.print("Computer saw " + str((depth + 1 // 2)) + " moves ahead.")

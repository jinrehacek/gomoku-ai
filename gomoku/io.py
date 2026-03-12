# MY RICH IMPORTS
from rich.text import Text
from rich.console import Console
from rich.table import Table
from rich.box import MINIMAL as TABLE_STYLE
from rich.prompt import Prompt


# GOMOKU imports
from gomoku.board import Board
from gomoku.engine import iterative_deepening, get_best_move

import time
from concurrent.futures import ThreadPoolExecutor

# the main hero, bridges stdout with whatever shit i have
cons = Console()


def create_table(board: Board) -> Table:
    size = board.LENGTH
    grid = Table(show_header=False, show_edge=False, show_lines=True, box=TABLE_STYLE)
    mapa = {0: Text(""), 1: Text("X", style="bold red"), 2: Text("O", style="bold blue")}

    pismenka = [chr(ord("a") + x) for x in range(size)]
    numbers = [str(x) for x in range(1, size + 1)]
    for i in range(size + 1):
        if i == 0:
            grid.add_column(justify="right", width=2)
        else:
            grid.add_column(justify="center", width=1)

    # MAPUJE JAK SE ZOBRAZI KAMENY

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


def board_coords_to_xy(s: str) -> tuple[int, int]:
    x = int(s[1:]) - 1
    y = ord(s[0].lower()) - ord("a")
    return x, y


def play(size=15, fixed=0, our_time=10):
    """
    the defaults are useles ther is always passed defualt from main.py
    """
    board = Board(size)
    cons.clear()
    tabulka = create_table(board)
    cons.print(tabulka)
    while True:
        user_move = Prompt.ask("Enter your move (g8, a5, ...)")

        board.place(*board_coords_to_xy(user_move))
        state = board.is_over()

        cons.clear()
        tabulka = create_table(board)
        cons.print(tabulka)

        if state > 0:
            cons.print(str(state), style="bold magenta")
            break

        # COMPLET SEARCH PATTERNS jsou computed on IMPORT, tedy jen JEDNOU
        start = time.time()
        # ai_move, depth = iterative_deepening(board, player=1, given_time=10)

        cons.print("\n")
        if fixed == 0:
            with cons.status("[bold cyan]Bot is thinking...", spinner="monkey"):
                with ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(iterative_deepening, board, 1, our_time)  # board, player, given_time
                    while not future.done():
                        time.sleep(0.05)  # keeps loop responsive
                    ai_move, depth = future.result()
        else:
            ai_move = get_best_move(board, 1, fixed)
            depth = fixed
        board.place(*ai_move)
        state = board.is_over()
        if state > 0:
            cons.print(str(state), style="bold magenta")
            break

        cons.clear()
        tabulka = create_table(board)
        cons.print(tabulka)
        current_time = time.time()
        zprava = Text()
        cons.print("Bot thought for " + str((current_time - start)) + "seconds")
        cons.print("Bot went " + str((depth)) + "levels deep")

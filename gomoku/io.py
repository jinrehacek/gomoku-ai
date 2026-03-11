# tady se budu bavit pres Rich a TUI s uzivatelem  a kodem a budu volat engine, Board a podobne

from math import cos
from time import sleep
from rich import style
from rich.panel import Panel
import rich.box

from rich.layout import Layout


# MY RICH IMPORTS
from rich.text import Text
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from gomoku.board import Board
from gomoku.engine import iterative_deepening


# the main hero, bridges stdout with whatever shit i have
cons = Console()


def create_table(board: Board, last_placed: tuple[int, int] | None = None) -> Table:
    size = board.LENGTH
    grid = Table(show_header=False, show_edge=False, show_lines=False, box=None)

    # vertically numbers, horizontally alphabet

    pismenka = [chr(ord("a") + x) for x in range(size)]
    numbers = [str(x) for x in range(1, size + 1)]  # WARNING:IS FROM 1-15

    for i in range(size + 1):
        grid.add_column(justify="center", width=3 if i == 0 else 1)

    # MAPUJE JAK SE ZOBRAZI KAMENY
    mapa = {0: Text("."), 1: Text("X", style="bold red"), 2: Text("O", style="bold indigo")}

    grid.add_row(Text(" "), *pismenka)

    for i in range(0, size):
        row = board.data[i]
        new_row = [mapa[x] for x in row]
        grid.add_row(Text(numbers[i], style=""), *new_row)

    if board.last_placed is not None:
        # TODO: pridat dasli brykule
        l_x, l_y = board.last_placed

    return grid


def board_coords_to_xy(fancy: str) -> tuple[int, int]:
    x = ord(fancy[0].lower()) - ord("a")
    y = int(fancy[1]) - 1
    return x, y


board = Board()
while True:
    cons.clear()

    tabulka = create_table(board)
    cons.print(tabulka)

    user_move = Prompt.ask("Enter your move (g8, a5, ...):")

    board.place(*board_coords_to_xy(user_move))
    state = board.is_over()
    if state > 0:
        cons.print(str(state), style="bold magenta")
        break

    ai_move = iterative_deepening(board, player=1)
    board.place(*ai_move)
    if state > 0:
        cons.print(str(state), style="bold magenta")
        break

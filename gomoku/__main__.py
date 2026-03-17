import argparse

from rich.text import Text

from gomoku.board import Board
from gomoku.io import ai_move, ai_swap, ai_vs_ai_swap, cons, human_move, human_swap, pick_mode_and_swap, redraw_board

parser = argparse.ArgumentParser(description="Gomoku game and AI playable in terminal")
parser.add_argument("-s", "--size", help="Set size of board (default is 15)", type=int, default=15)
parser.add_argument("-w", "--win", help="Set winning stones lenght", type=int, default=5)
parser.add_argument("-t", "--time", help="Seconds to think (1 or more)", type=int, default=10)
parser.add_argument("-f", "--fixed", help="If given sets minimax to fixed depth & ignores time limit", type=int, default=0)
parser.add_argument("-m", "--ai", help="AI vs. AI mode", action="store_true")
parser.add_argument("--swap", help="Who does Swap2 (1) You, (2) AI", type=int, default=0)


args = parser.parse_args()

# Making sure arguments are sensible values
if args.time < 1:
    raise Exception("Negative or extremely small time given. Please try again!")
if args.fixed < 0:
    raise Exception("Negative fixed depth given. Are you joking, or mentally challenged?")
if args.size < 2:
    raise Exception("Absurd size of board given. Don't do that again. Thx")
if args.win < 1:
    raise Exception("Absurd win lenght, please be for real!")

assert args.swap in [0, 1, 2]


def play_human_vs_ai(board: Board, human_player):
    while True:
        if board.turn == human_player:
            human_move(board)
            state = board.is_over()
            if state > 0:
                cons.print(
                    Text(
                        "Human Won",
                        style="bold blink",
                    )
                )
                break
        else:
            ai_move(board, time_limit=args.time, fixed=args.fixed)
            state = board.is_over()
            if state > 0:
                cons.print(
                    "[bold blink red]🤖 The ROBOT Won 🤖[/bold blink red] "
                    "[bold blink white]it's over for humanity.[/bold blink white]"
                )
                break


def play_ai_vs_ai(board: Board):
    ai_vs_ai_swap(board, time_limit=args.time, fixed=args.fixed)
    while True:
        ai_move(board, time_limit=args.time, fixed=args.fixed)
        state = board.is_over()
        if state > 0:
            cons.print(
                "[bold blink red]🤖 One ROBOT Won 🤖[/bold blink red] "
                "[bold blink white]the silicon wars are over.[/bold blink white]"
            )
            break


def main():
    board = Board(size=args.size, win_len=args.win)

    # Getting user's choice on mode and swap
    if not args.ai and not args.swap:
        mode, swap_maker = pick_mode_and_swap()
    elif args.swap and not args.ai:
        swap_maker = args.swap
        mode = 1
    else:
        mode, swap_maker = 2, 0

    # Swap2 Handling
    if swap_maker == 1:
        human_player = human_swap(board, args.time, args.fixed)
    elif swap_maker == 2:
        human_player = ai_swap(board, time_limit=args.time, fixed=args.fixed)
    else:
        human_player = None

    # AI vs. AI mode
    if mode == 2:
        play_ai_vs_ai(board)
        return

    # Human vs. AI mode
    redraw_board(board)
    play_human_vs_ai(board, human_player)


if __name__ == "__main__":
    main()

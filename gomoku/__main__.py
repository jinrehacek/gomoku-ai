from rich.text import Text
from gomoku.board import Board
from gomoku.io import human_move, ai_move, cons, redraw_board, pick_mode_and_swap, get_inp_num
import argparse


parser = argparse.ArgumentParser(description="Gomoku game and AI playable in terminal")
parser.add_argument("-s", "--size", help="Set size of board (default is 15)", type=int, default=15)
parser.add_argument("-t", "--time", help="Seconds to think", type=int, default=10)
parser.add_argument("-f", "--fixed", help="If given sets minimax to fixed depth & ignores time limit", type=int, default=0)
parser.add_argument("-w", "--win", help="Set winning stones lenght", type=int, default=5)
parser.add_argument("-m", "--ai", help="AI vs. AI mode", action="store_true")


args = parser.parse_args()


def main():
    board = Board(size=args.size, win_len=args.win)
    a = pick_mode_and_swap(board)
    cons.print(str(a))
    redraw_board(board)
    while True:
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

        ai_move(board, time_limit=args.time, fixed=args.fixed)
        state = board.is_over()
        if state > 0:
            cons.print(
                Text(
                    "Human Won",
                    style="bold blink",
                )
            )
            break


if __name__ == "__main__":
    main()

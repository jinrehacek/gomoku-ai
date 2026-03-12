from gomoku.io import play
import argparse


parser = argparse.ArgumentParser(description="Gomoku game and AI playable in terminal")
parser.add_argument("-s", "--size", help="Set size of board (default is 15)", type=int)
parser.add_argument("-f", "--fixed", help="If given sets minimax to fixed depth", type=int, default=0)
parser.add_argument("-t", "--time", help="Seconds to think", type=int, default=10)


args = parser.parse_args()
# TODO: fix this shit, this is horrible practice


def main():
    if args.size is None:
        size = 15
    else:
        size = args.size
    play(size=size, our_time=args.time, fixed=args.fixed)


if __name__ == "__main__":
    main()

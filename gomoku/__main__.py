import gomoku.io
import argparse


parser = argparse.ArgumentParser(description="Gomoku game and AI playable in terminal")
parser.add_argument("-s", "--size", help="Set size of board (default is 15)")

args = parser.parse_args()
# TODO: fix this shit, this is horrible practice


def main():
    if args.size is None:
        size = 15
    else:
        size = int(args.size)
    gomoku.io.play(size=size)


if __name__ == "__main__":
    main()

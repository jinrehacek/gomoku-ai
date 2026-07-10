import argparse
import os

from gomoku.tui import GomokuApp
from gomoku.web import GomokuServer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gomoku game with Textual UI")
    parser.add_argument("-s", "--size", help="Set size of board (default is 15)", type=int, default=15)
    parser.add_argument("-w", "--win", help="Set winning stones length", type=int, default=5)
    parser.add_argument("-t", "--time", help="Seconds to think (1 or more)", type=int, default=10)
    parser.add_argument(
        "-f",
        "--fixed",
        help="If given sets minimax to fixed depth and ignores time limit",
        type=int,
        default=0,
    )
    parser.add_argument("-m", "--ai", help="AI vs AI mode", action="store_true")
    parser.add_argument("--swap", help="Who does Swap2 (1) You, (2) AI, (0) random", type=int, default=0)
    parser.add_argument(
        "--serve",
        help="Serve the Textual app over HTTP for browser clients",
        action="store_true",
    )
    parser.add_argument("--host", help="Host for --serve mode", type=str, default="0.0.0.0")
    parser.add_argument("--port", help="Port for --serve mode", type=int, default=8000)
    parser.add_argument(
        "--url",
        help="Public URL for reverse proxies. Can also be set via PUBLIC_URL env var.",
        type=str,
        default=os.environ.get("PUBLIC_URL"),
    )

    args = parser.parse_args()

    if args.time < 1:
        raise Exception("Negative or extremely small time given. Please try again!")
    if args.fixed < 0:
        raise Exception("Negative fixed depth given.")
    if args.size < 2:
        raise Exception("Absurd size of board given.")
    if args.win < 1:
        raise Exception("Absurd win length, please be for real!")
    if args.swap not in [0, 1, 2]:
        raise Exception("Swap must be 0, 1 or 2.")
    if args.port < 1 or args.port > 65535:
        raise Exception("Port must be between 1 and 65535.")

    return args


def main() -> None:
    args = parse_args()
    mode = 2 if args.ai else 1

    if args.serve:
        command = (
            f"python -m gomoku --size {args.size} --win {args.win} --time {args.time} --fixed {args.fixed} --swap {args.swap}"
        )
        if mode == 2:
            command += " --ai"

        public_url = args.url if args.url else f"http://{args.host}:{args.port}"
        public_url = public_url.rstrip("/")

        server = GomokuServer(
            command=command,
            host=args.host,
            port=args.port,
            title="Gomoku",
            public_url=public_url,
            default_font_size=14,
        )
        server.serve()
        return

    app = GomokuApp(
        size=args.size,
        win_len=args.win,
        time_limit=args.time,
        fixed=args.fixed,
        mode=mode,
        swap=args.swap,
    )
    app.run()


if __name__ == "__main__":
    main()

from __future__ import annotations

import copy
import dataclasses
import threading
import time
from random import randint
from typing import cast

from textual.binding import Binding
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import MouseDown
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Static, Button, Label

from gomoku.board import Board, Coord, Player
from gomoku.engine import COMPLETE_PATTERNS, eval_board, get_best_move, iterative_deepening, minimax
from gomoku.io import xy_to_board_coords


class GameOverScreen(ModalScreen[bool]):
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg

    def compose(self) -> ComposeResult:
        with Vertical(id="game_over_dialog"):
            yield Label(self.msg, id="game_over_message")
            with Horizontal(id="game_over_buttons"):
                yield Button("Play Again", id="restart_btn", variant="primary")
                yield Button("Quit", id="quit_btn", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "restart_btn":
            self.dismiss(True)
        else:
            self.dismiss(False)


class BoardView(Static):
    can_focus = True

    def _grid_metrics(self, board_size: int) -> tuple[int, int, int, int]:
        # Square grid
        # Each cell is 4 characters wide (" X " + "│").
        # Each row takes 2 lines (content line + mid border).
        cell_w = 4
        row_stride = 2

        board_w = 4 + (board_size * cell_w) + 1
        board_h = 2 + (board_size * row_stride)

        usable_w = max(20, self.size.width - 2)
        usable_h = max(8, self.size.height - 2)

        left_pad = max(0, (usable_w - board_w) // 2)
        top_pad = max(0, (usable_h - board_h) // 2)

        return cell_w, row_stride, left_pad, top_pad

    def render(self) -> Text:
        app = cast("GomokuApp", self.app)
        size = app.board.LENGTH
        cursor_x, cursor_y = app.cursor
        last_move = app.board.history[-1] if app.board.history else None
        last_x, last_y = last_move if last_move is not None else (-1, -1)

        cell_w, row_stride, left_pad, top_pad = self._grid_metrics(size)
        self._last_metrics = (cell_w, row_stride, left_pad, top_pad)

        out = Text()

        if top_pad > 0:
            out.append("\n" * top_pad)

        # Header
        out.append(" " * left_pad)
        out.append("   ")  # 3 spaces to perfectly align the letters over the 3-char wide cells
        for y in range(size):
            label_style = "bold #cbd5e1"
            if y == last_y:
                label_style = "bold #34d399"
            out.append(f"  {chr(ord('a') + y)} ", style=label_style)
        out.append("\n")

        # Top border
        out.append(" " * left_pad)
        out.append("   ┌")
        out.append("┬".join(["───"] * size))
        out.append("┐\n")

        for x in range(size):
            # Row number
            out.append(" " * left_pad)
            row_style = "bold #cbd5e1"
            if x == last_x:
                row_style = "bold #34d399"
            out.append(f"{x + 1:>2} ", style=row_style)

            out.append("│")
            for y in range(size):
                stone = app.board.data[x][y]
                if stone == 0:
                    char = " "
                    if x == last_x or y == last_y:
                        style = "#34d399"
                    else:
                        style = ""
                elif stone == 1:
                    char = "X"
                    style = "bold #ff4f9a"
                else:
                    char = "O"
                    style = "bold #4fd6ff"

                if (x, y) == (last_x, last_y):
                    style = "bold #34d399"

                cell_text = Text(f" {char} ", style=style)
                if (x, y) == (cursor_x, cursor_y):
                    cell_text.stylize("on #1f4d45")

                out.append(cell_text)
                out.append("│")

            out.append("\n")

            if x < size - 1:
                out.append(" " * left_pad)
                out.append("   ├")
                out.append("┼".join(["───"] * size))
                out.append("┤\n")

        # Bottom border
        out.append(" " * left_pad)
        out.append("   └")
        out.append("┴".join(["───"] * size))
        out.append("┘")

        return out

    def on_mouse_down(self, event: MouseDown) -> None:
        app = cast("GomokuApp", self.app)
        content_offset = event.get_content_offset(self)
        if content_offset is None:
            return

        cell_w, row_stride, left_pad, top_pad = getattr(self, "_last_metrics", self._grid_metrics(app.board.LENGTH))

        # Y offset: subtract top_pad, header (1), top border (1)
        row = content_offset.y - top_pad - 2
        # X offset: subtract left_pad, row number area (4)
        col = content_offset.x - left_pad - 4

        if row < 0 or col < 0:
            return

        board_row = row // row_stride
        board_col = col // cell_w

        if board_row < 0 or board_row >= app.board.LENGTH:
            return
        if board_col < 0 or board_col >= app.board.LENGTH:
            return

        event.stop()
        event.prevent_default()

        app.cursor = (board_row, board_col)
        app.attempt_place(board_row, board_col)


class GomokuApp(App):
    CSS = """
    Screen {
        layout: vertical;
        background: #1b1f33;
        color: #dbe4ff;
    }

    #main {
        height: 1fr;
    }

    BoardView {
        width: 1fr;
        height: 100%;
        content-align: left top;
        border: round #7aa2f7;
        background: #1f2440;
        padding: 1;
    }

    #sidebar {
        width: 34;
        min-width: 32;
        height: 100%;
        border: round #7aa2f7;
        background: #1f2440;
        padding: 1 2;
    }

    #status {
        height: auto;
    }

    #help {
        height: auto;
        margin-top: 2;
    }

    GameOverScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #game_over_dialog {
        padding: 2 4;
        border: thick $background 80%;
        background: #1f2440;
        width: 44;
        height: auto;
        align: center middle;
    }

    #game_over_message {
        text-align: center;
        text-style: bold;
        padding-bottom: 2;
        width: 100%;
    }

    #game_over_buttons {
        align: center middle;
        height: auto;
    }

    Button {
        margin: 0 2;
    }
    """

    BINDINGS = [
        Binding("up", "cursor_up", "Cursor up", show=False),
        Binding("down", "cursor_down", "Cursor down", show=False),
        Binding("left", "cursor_left", "Cursor left", show=False),
        Binding("right", "cursor_right", "Cursor right", show=False),
        Binding("w", "cursor_up", "Cursor up", show=False),
        Binding("s", "cursor_down", "Cursor down", show=False),
        Binding("a", "cursor_left", "Cursor left", show=False),
        Binding("d", "cursor_right", "Cursor right", show=False),
        Binding("space", "place", "Place", show=False),
        Binding("enter", "place", "Place"),
        Binding("1", "choice_one", "Choice 1"),
        Binding("2", "choice_two", "Choice 2"),
        Binding("3", "choice_three", "Choice 3"),
        Binding("p", "toggle_autoplay", "Pause/Play AI"),
        Binding("r", "restart", "Restart"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        size: int = 15,
        win_len: int = 5,
        time_limit: int = 10,
        fixed: int = 0,
        mode: int = 1,
        swap: int = 0,
    ):
        super().__init__()
        self.board_size = size
        self.win_len = win_len
        self.time_limit = time_limit
        self.fixed = fixed
        self.mode = mode
        self.swap = swap

        self.board = Board(size=self.board_size, win_len=self.win_len)
        self.cursor: Coord = (self.board_size // 2, self.board_size // 2)
        self.human_player: Player | None = None
        self.phase = "init"
        self.info_message = ""
        self.pending_setup: list[Coord] = []
        self.ai_busy = False
        self.autoplay = True
        self.last_ai_stats = ""

    def compose(self) -> ComposeResult:
        # yield Header(show_clock=True)
        with Horizontal(id="main"):
            yield BoardView(id="board")
            with Vertical(id="sidebar"):
                yield Static(id="status")
                yield Static(id="help")
        yield Footer()

    def on_mount(self) -> None:
        self.start_game()
        self.refresh_footer_bindings()

    def start_game(self) -> None:
        self.board = Board(size=self.board_size, win_len=self.win_len)
        self.cursor = (self.board_size // 2, self.board_size // 2)
        self.human_player = None
        self.phase = "init"
        self.info_message = ""
        self.pending_setup = []
        self.ai_busy = False
        self.autoplay = True
        self.last_ai_stats = ""

        if self.mode == 2:
            self.setup_ai_vs_ai()
        else:
            if self.swap == 0:
                self.phase = "choose_swap"
                self.info_message = "Who should place the first 3 stones?"
            elif self.swap == 1:
                self.phase = "human_swap_3"
                self.info_message = "Swap-2: place 3 stones by clicking cells (X, O, X)."
            else:
                self.setup_ai_swap()

        self.refresh_ui()

    def refresh_footer_bindings(self) -> None:
        remapped: dict[str, list[Binding]] = {}

        for key, bindings in self._bindings.key_to_bindings.items():
            for binding in bindings:
                description = binding.description
                show = binding.show

                if key in {"1", "2", "3"}:
                    show = self.phase in {"ai_swap_choice", "choose_swap"}

                    if self.phase == "ai_swap_choice":
                        if key == "1":
                            description = "Choose X"
                        elif key == "2":
                            description = "Choose O"
                        elif key == "3":
                            description = "Add 2 stones"
                    elif self.phase == "choose_swap":
                        if key == "1":
                            description = "You start"
                        elif key == "2":
                            description = "AI starts"
                        elif key == "3":
                            description = "Random"
                    else:
                        show = False

                if key == "p":
                    show = self.mode == 2 and self.phase == "play"
                    if self.mode == 2:
                        description = "Pause AI" if self.autoplay else "Resume AI"

                if key == "enter":
                    if self.phase in {"human_swap_3", "ai_swap_add2", "play"}:
                        description = "Place"
                        show = True
                    else:
                        show = False

                new_binding = dataclasses.replace(binding, description=description, show=show)
                remapped.setdefault(key, []).append(new_binding)

        self._bindings.key_to_bindings = remapped
        self.refresh_bindings()

    def setup_ai_swap(self) -> None:
        length = self.board.LENGTH
        half = max(1, length // 4)
        self.place_with_fallback(half, half)
        self.place_with_fallback(length // 2 + randint(-half, half), length // 2)
        self.place_with_fallback(length - half - 1, length - half - 1 + randint(-half, half))
        self.phase = "ai_swap_choice"
        self.info_message = "Choose: [1] play X, [2] play O, [3] add two stones."

    def setup_ai_vs_ai(self) -> None:
        length = self.board.LENGTH
        half = max(1, length // 4)
        self.place_with_fallback(half, half)
        self.place_with_fallback(length // 2 + randint(-half, half), length // 2)
        self.place_with_fallback(length - half - 1, length - half - 1 + randint(-half, half))

        current_player = cast(Player, self.board.turn)
        opening_eval = minimax(self.board, 4, current_player, curr_eval=eval_board(self.board, COMPLETE_PATTERNS))
        ai_player = cast(Player, 0 if opening_eval > 0 else 1)

        self.phase = "play"
        if ai_player != current_player:
            self.info_message = "Second AI chose the other side and played one move."
            self.trigger_ai_turn()
        else:
            self.info_message = "Second AI chose the side to move now."
            self.trigger_ai_turn()

    def place_with_fallback(self, x: int, y: int) -> None:
        x = max(0, min(self.board.LENGTH - 1, x))
        y = max(0, min(self.board.LENGTH - 1, y))
        if self.board.data[x][y] == 0:
            self.board.place(x, y)
            return

        for row in range(self.board.LENGTH):
            for col in range(self.board.LENGTH):
                if self.board.data[row][col] == 0:
                    self.board.place(row, col)
                    return

    def action_cursor_up(self) -> None:
        self.cursor = (max(0, self.cursor[0] - 1), self.cursor[1])
        self.refresh_ui()

    def action_cursor_down(self) -> None:
        self.cursor = (min(self.board.LENGTH - 1, self.cursor[0] + 1), self.cursor[1])
        self.refresh_ui()

    def action_cursor_left(self) -> None:
        self.cursor = (self.cursor[0], max(0, self.cursor[1] - 1))
        self.refresh_ui()

    def action_cursor_right(self) -> None:
        self.cursor = (self.cursor[0], min(self.board.LENGTH - 1, self.cursor[1] + 1))
        self.refresh_ui()

    def action_place(self) -> None:
        self.attempt_place(*self.cursor)

    def action_choice_one(self) -> None:
        self.handle_choice(1)

    def action_choice_two(self) -> None:
        self.handle_choice(2)

    def action_choice_three(self) -> None:
        self.handle_choice(3)

    def action_toggle_autoplay(self) -> None:
        if self.mode != 2 or self.phase == "game_over":
            return
        self.autoplay = not self.autoplay
        state = "resumed" if self.autoplay else "paused"
        self.info_message = f"AI vs AI autoplay {state}."
        if self.autoplay and not self.ai_busy:
            self.trigger_ai_turn()
        self.refresh_footer_bindings()
        self.refresh_ui()

    def action_restart(self) -> None:
        self.start_game()

    def handle_choice(self, choice: int) -> None:
        if self.phase == "choose_swap":
            if choice == 3:
                choice = randint(1, 2)

            if choice == 1:
                self.phase = "human_swap_3"
                self.info_message = "Swap-2: place 3 stones by clicking cells (X, O, X)."
            else:
                self.setup_ai_swap()
            self.refresh_footer_bindings()
            self.refresh_ui()
        elif self.phase == "ai_swap_choice":
            current_player = cast(Player, self.board.turn)
            if choice == 2:
                self.human_player = current_player
                self.phase = "play"
                self.info_message = "You chose O side (side to move now). Your move."
            elif choice == 1:
                self.human_player = cast(Player, current_player ^ 1)
                self.phase = "play"
                self.info_message = "You chose X side. AI now makes the next move."
                self.trigger_ai_turn()
            elif choice == 3:
                self.phase = "ai_swap_add2"
                self.pending_setup = []
                self.info_message = "Add 2 stones now by clicking cells in order: X then O."
            self.refresh_footer_bindings()
            self.refresh_ui()

    def attempt_place(self, x: int, y: int) -> None:
        self.cursor = (x, y)

        if self.ai_busy:
            self.info_message = "AI is thinking. Please wait."
            self.refresh_ui()
            return

        if self.phase == "game_over":
            self.info_message = "Game is over. Press R to restart."
            self.refresh_ui()
            return

        if x < 0 or y < 0 or x >= self.board.LENGTH or y >= self.board.LENGTH:
            self.info_message = "Move out of bounds."
            self.refresh_ui()
            return

        if self.board.data[x][y] != 0:
            self.info_message = "Square occupied."
            self.refresh_ui()
            return

        if self.phase == "human_swap_3":
            self.board.place(x, y)
            self.pending_setup.append((x, y))
            if len(self.pending_setup) == 3:
                self.pending_setup = []
                self.finish_human_swap()
            else:
                self.info_message = f"Swap-2 setup: placed {len(self.board.history)} / 3 stones."
            self.refresh_footer_bindings()
            self.refresh_ui()
            return

        if self.phase == "ai_swap_add2":
            self.board.place(x, y)
            self.pending_setup.append((x, y))
            if len(self.pending_setup) == 2:
                self.pending_setup = []
                self.finish_human_swap()
            else:
                self.info_message = "Add one more stone to finish setup."
            self.refresh_footer_bindings()
            self.refresh_ui()
            return

        if self.phase != "play":
            self.info_message = "Not in playable phase yet."
            self.refresh_ui()
            return

        if self.mode == 1 and self.human_player != self.board.turn:
            self.info_message = "It is AI turn."
            self.refresh_ui()
            return

        self.board.place(x, y)
        if self.check_game_over():
            self.refresh_ui()
            return

        self.info_message = "Move accepted."
        if self.mode == 1 and self.human_player != self.board.turn:
            self.trigger_ai_turn()
        elif self.mode == 2 and self.autoplay:
            self.trigger_ai_turn()
        self.refresh_ui()

    def finish_human_swap(self) -> None:
        current_player = cast(Player, self.board.turn)
        opening_eval = minimax(self.board, 4, current_player, curr_eval=eval_board(self.board, COMPLETE_PATTERNS))
        ai_player = cast(Player, 0 if opening_eval > 0 else 1)
        self.human_player = cast(Player, ai_player ^ 1)
        self.phase = "play"

        if ai_player == current_player:
            self.info_message = "Computer chose side to move now."
            self.trigger_ai_turn()
        else:
            self.info_message = "Computer chose the other side. Your move."

        self.refresh_footer_bindings()

    def trigger_ai_turn(self) -> None:
        if self.ai_busy or self.phase != "play":
            return
        if self.mode == 2 and not self.autoplay:
            return

        self.ai_busy = True
        self.info_message = "AI is thinking..."
        self.refresh_ui()

        as_player = cast(Player, self.board.turn)
        snapshot = copy.deepcopy(self.board)
        thread = threading.Thread(target=self.compute_ai_move, args=(snapshot, as_player), daemon=True)
        thread.start()

    def compute_ai_move(self, snapshot: Board, as_player: Player) -> None:
        start = time.time()
        if self.fixed == 0:
            move, depth = iterative_deepening(snapshot, as_player, self.time_limit)
        else:
            move = get_best_move(snapshot, as_player, self.fixed)
            depth = self.fixed
        elapsed = round(time.time() - start, 2)
        self.call_from_thread(self.apply_ai_move, as_player, move, depth, elapsed)

    def apply_ai_move(self, as_player: Player, move: Coord, depth: int, elapsed: float) -> None:
        self.ai_busy = False

        if self.phase != "play":
            self.refresh_ui()
            return
        if self.board.turn != as_player:
            self.refresh_ui()
            return

        self.board.place(*move)
        move_str = xy_to_board_coords(*move)
        self.last_ai_stats = f"Move:  [bold #34d399]{move_str}[/]\nDepth: [bold]{depth}[/]\nTime:  [bold]{elapsed}s[/]"
        self.info_message = f"AI played {move_str}."

        if self.check_game_over():
            self.refresh_ui()
            return

        if self.mode == 2 and self.autoplay:
            self.trigger_ai_turn()

        self.refresh_ui()

    def check_game_over(self) -> bool:
        state = self.board.is_over()
        if state == 0:
            return False

        self.phase = "game_over"
        self.ai_busy = False

        if state == 3:
            msg = "Game over: Draw!"
            self.info_message = msg
        else:
            winner_player = cast(Player, state - 1)
            if self.mode == 1 and self.human_player is not None:
                if winner_player == self.human_player:
                    msg = "Game over: human won!"
                else:
                    msg = "Game over: AI won!"
            else:
                msg = f"Game over: {'X' if winner_player == 0 else 'O'} won!"
            self.info_message = msg

        self.push_screen(GameOverScreen(msg), self.handle_game_over_result)
        self.refresh_footer_bindings()
        return True

    def handle_game_over_result(self, restart: bool) -> None:
        if restart:
            self.start_game()
        else:
            self.exit()

    def refresh_ui(self) -> None:
        board_widget = self.query_one(BoardView)
        board_widget.refresh()
        self.refresh_footer_bindings()

        turn_text = "[bold #ff4f9a]X[/]" if self.board.turn == 0 else "[bold #4fd6ff]O[/]"
        human_side = "?"
        if self.human_player == 0:
            human_side = "[bold #ff4f9a]X[/]"
        elif self.human_player == 1:
            human_side = "[bold #4fd6ff]O[/]"
        elif self.mode == 1:
            human_side = "Not chosen"

        mode_text = "Human vs AI" if self.mode == 1 else "AI vs AI"

        status = Text.from_markup(
            f"[bold underline]Game Info[/]\n\nMode:  {mode_text}\nPhase: {self.phase}\nTurn:  {turn_text}\n"
        )
        if self.mode == 1:
            status.append_text(Text.from_markup(f"Your side: {human_side}\n"))
        status.append(f"Moves played: {len(self.board.history)}\n\n")
        status.append_text(Text.from_markup(f"[bold #cbd5e1]{self.info_message}[/]\n\n"))

        if hasattr(self, "last_ai_stats") and self.last_ai_stats:
            status.append_text(Text.from_markup(f"[bold underline]Last AI Move[/]\n{self.last_ai_stats}\n\n"))

        self.query_one("#status", Static).update(status)

        contextual = Text()
        contextual.append("Now\n", style="bold underline")
        if self.phase == "choose_swap":
            contextual.append("- [1]: You place 3 stones\n")
            contextual.append("- [2]: AI places 3 stones\n")
            contextual.append("- [3]: Random choice\n")
        elif self.phase == "ai_swap_choice":
            contextual.append("- [1]: Choose X\n")
            contextual.append("- [2]: Choose O\n")
            contextual.append("- [3]: Add 2 stones\n")
        elif self.phase == "ai_swap_add2":
            contextual.append("- Click 2 cells: X then O\n")
        elif self.phase == "human_swap_3":
            contextual.append("- Click 3 cells: X, O, X\n")
        elif self.phase == "play":
            if self.mode == 2:
                contextual.append("- [P]: Pause/Resume AI autoplay\n")
            else:
                contextual.append("- Your turn: click or Enter\n")
        elif self.phase == "game_over":
            contextual.append("- [R]: Restart game\n")

        self.query_one("#help", Static).update(contextual)

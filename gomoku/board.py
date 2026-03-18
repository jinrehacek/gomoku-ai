# Default values for the Board
from typing import Literal

WHITE_TURN, BLACK_TURN = 0, 1
WHITE_STONE, BLACK_STONE = 1, 2
SIZE = 15
WIN_LEN = 5

Coord = tuple[int, int]
Player = Literal[0] | Literal[1]


class Board:
    def __init__(self, size=SIZE, win_len=WIN_LEN) -> None:
        """
        default size = 15; WIN_LEN = 5
        .data = 2D array (array of rows)
        """
        self.data = [[0 for _ in range(size)] for _ in range(size)]
        # 0 = na tahu bily; 1 = na tahu cerny
        self.turn = 0
        self.LENGTH = size
        self.WINNING_LENGTH = win_len
        # Coords of last placed stone
        self.history: list[Coord] = []

    def place(self, x: int, y: int):
        """
        beware - parameters are not intuitive
        x = row
        y = column
        """
        if self.data[x][y] != 0:
            raise Exception("Placing stone on already occupied square!")
        else:
            self.data[x][y] = self.turn + 1
            self.turn ^= 1  # obrati hodnotu turn
            self.history.append((x, y))

    def remove_stone(self, x, y):
        """
        remove (preferably last placed) stone from board
        flips self.turn
        errors when trying to remove nothing
        """
        if self.data[x][y] == 0:
            raise Exception("Cannot remove stone from empty square!")
        else:
            self.data[x][y] = 0
            self.turn ^= 1

    def undo_move(self):
        if len(self.history) == 0:
            raise Exception("No move has been played!")
        else:
            x, y = self.history.pop()
            self.remove_stone(x, y)

    def is_full(self) -> bool:
        """
        returns True when stone in every square
        """
        for x in range(self.LENGTH):
            for y in range(self.LENGTH):
                if self.data[x][y] == 0:
                    return False
        return True

    def check_line(self, line: list[int], IN_ROW=None) -> int:
        """
        checks if there is a win in given line (row, col, diagonal)
        0: no win
        1: white won
        2: black won
        """
        if IN_ROW is None:
            IN_ROW = self.WINNING_LENGTH
        
        together = 0
        last = 0
        for i in range(len(line)):
            x = line[i]
            if x != 0:
                if x == last:
                    together += 1
                else:
                    if together == IN_ROW:
                        return last
                    last = x
                    together = 1
            else:
                if together == IN_ROW:
                    return last
                last = 0
                together = 0
                
        if together == IN_ROW:
            return last
            
        return 0

    def _get_xy_row(self, x: int) -> list[int]:
        return self.data[x]

    def _get_xy_col(self, y: int) -> list[int]:
        return [self.data[i][y] for i in range(self.LENGTH)]

    def _get_xy_diag1(self, x: int, y: int) -> list[int]:
        posun = min(x, y)
        diag: list[int] = []
        n_x, n_y = x - posun, y - posun
        while n_x < self.LENGTH and n_y < self.LENGTH:
            diag.append(self.data[n_x][n_y])
            n_x, n_y = n_x + 1, n_y + 1
        return diag

    def _get_xy_diag2(self, x: int, y: int) -> list[int]:
        diag = []
        n_x, n_y = x, y
        while n_x + 1 < self.LENGTH and n_y - 1 >= 0:
            n_x, n_y = n_x + 1, n_y - 1

        while n_x >= 0 and n_y < self.LENGTH:
            diag.append(self.data[n_x][n_y])
            n_x, n_y = n_x - 1, n_y + 1
        return diag

    def _get_all_rows(self):
        for i in range(self.LENGTH):
            yield self.data[i]

    def _get_all_columns(self):
        for i in range(self.LENGTH):
            yield [self.data[x][i] for x in range(self.LENGTH)]

    def _get_all_diagonals(self, min_pattern_len=None):
        if min_pattern_len is None:
            min_pattern_len = self.WINNING_LENGTH

        # DIAGONALS /
        diagonal_starts = [(x, 0) for x in range(min_pattern_len - 1, self.LENGTH)] + [
            (self.LENGTH - 1, y) for y in range(0, self.LENGTH - min_pattern_len + 1)
        ]
        for x, y in diagonal_starts:
            line = []
            while y < self.LENGTH:
                line.append(self.data[x][y])
                y, x = y + 1, x - 1
            yield line

        # DIAGONALS \
        diagonal_starts1 = [(0, i) for i in range(0, self.LENGTH - min_pattern_len + 1)]
        diagonal_starts2 = [(i, 0) for i in range(1, self.LENGTH - min_pattern_len + 1)]
        diagonal_starts = diagonal_starts1 + diagonal_starts2

        for x, y in diagonal_starts:
            line = []
            while y < self.LENGTH and x < self.LENGTH:
                line.append(self.data[x][y])
                x, y = x + 1, y + 1
            yield line

    def _get_all_lines(self, min_pattern_len=None):
        """
        generator yieldign all lines that are atleast *min_pattern_len* long
        min_pattern_len is default WINNING_LENGTH
        """
        yield from self._get_all_columns()
        yield from self._get_all_rows()
        yield from self._get_all_diagonals(min_pattern_len)

    def is_over(self) -> int:
        """
        0: game is not over
        1: white won
        2: black won
        3: board is full, nobody won
        """

        if len(self.history) == 0:
            for line in self._get_all_lines(min_pattern_len=self.WINNING_LENGTH):
                state = self.check_line(line, IN_ROW=self.WINNING_LENGTH)
                if state > 0:
                    return state
            if self.is_full():
                return 3
            return 0

        lx, ly = self.history[-1]

        # ROWS
        line = self._get_xy_row(lx)
        state = self.check_line(line)
        if state > 0:
            return state

        # COLUMNS
        line = self._get_xy_col(ly)
        state = self.check_line(line)
        if state > 0:
            return state

        # DIAGONAL \
        diag = self._get_xy_diag1(lx, ly)
        state = self.check_line(diag)
        if state > 0:
            return state

        # DIAGONAL /
        diag = self._get_xy_diag2(lx, ly)
        state = self.check_line(diag)
        if state > 0:
            return state

        # check as last thing (highly unlikely to happen in game)
        if self.is_full():
            return 3

        return 0

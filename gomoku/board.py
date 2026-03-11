# Default values for the Board
WHITE_TURN, BLACK_TURN = 0, 1
WHITE_STONE, BLACK_STONE = 1, 2
SIZE = 15
WIN_LEN = 5


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
        self.last_placed = None

    def place(self, x, y):
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
            self.last_placed = (x, y)

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

    # func is unnecessray  - I think #F00
    # def undo_move(self):
    #     if self.last_placed is None:
    #         raise Exception("No move has been played!")
    #     else:
    #         x, y = self.last_placed
    #         self.remove_stone(x, y)

    def dev_print(self):
        sada = [".", "O", "X"]
        for i in range(self.LENGTH):
            line = self.data[i]
            a = [sada[j] for j in line]
            print(" ".join(a))  # space so its more square-ish

    def is_full(self) -> bool:
        """
        returns True when stone in every square
        """
        for x in range(self.LENGTH):
            for y in range(self.LENGTH):
                if self.data[x][y] == 0:
                    return False
        return True

    def check_line(self, inp_line: list[int], IN_ROW=None) -> int:
        """
        checks if there is a win in given line (row, col, diagonal)
        0: no win
        1: white won
        2: black won
        """
        if IN_ROW is None:
            IN_ROW = self.WINNING_LENGTH
        size = len(inp_line)
        line = inp_line + [0, 0]
        together = 0
        for i in range(size + 1):
            if together == IN_ROW and line[i] != line[i - 1]:
                return line[i - 1]

            if i == 0 and line[i]:
                together = 1
            elif line[i]:
                if line[i - 1] == line[i]:
                    together += 1
                else:
                    together = 1
        return 0

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

    # TODO: Refactor this shit so it checks just the lines with self.last_placed
    def is_over(self) -> int:
        """
        0: game is not over
        1: white won
        2: black won
        3: board is full, nobody won
        """
        # DIAGONALS /
        diagonal_starts = [(x, 0) for x in range(self.WINNING_LENGTH - 1, self.LENGTH)] + [
            (self.LENGTH - 1, y) for y in range(0, self.LENGTH - self.WINNING_LENGTH + 1)
        ]
        for x, y in diagonal_starts:
            line = []
            while y < self.LENGTH and x >= 0:
                line.append(self.data[x][y])
                y, x = y + 1, x - 1
            a = self.check_line(line)
            if a > 0:
                return a

        # DIAGONALS \ (small but negligible redundancy)
        for start in range(0, self.LENGTH - self.WINNING_LENGTH + 1):
            x, y = 0, start
            line1, line2 = [], []
            while x < self.LENGTH and y < self.LENGTH:
                line1.append(self.data[x][y])
                line2.append(self.data[y][x])
                x, y = x + 1, y + 1
            a, b = self.check_line(line1), self.check_line(line2)
            for answer in [a, b]:
                if answer:
                    return answer

        # ROWS
        for row in self.data:
            a = self.check_line(row)
            if a > 0:
                return a

        # COLUMNS
        for i in range(self.LENGTH):
            line = [self.data[x][i] for x in range(self.LENGTH)]
            a = self.check_line(line)
            if a > 0:
                return a

        # check as last thing (highly unlikely to happen in game)
        if self.is_full():
            return 3

        return 0

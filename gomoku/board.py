WHITE_STONE, BLACK_STONE = 1, 2
SIZE = 15


class Board:
    def __init__(self, size=SIZE) -> None:
        self.data = [[0 for _ in range(size)] for _ in range(size)]
        # 0 = na tahu bily; 1 = na tahu cerny
        self.turn = 0
        self.LENGTH = size

    def place(self, x, y, player=None):
        # if player is not None:
        #     self.turn = player # dovoli na pripadne upravit, kdo je na tahu

        if self.data[x][y] != 0:
            raise Exception("Placing stone on already occupied square!")
        else:
            self.data[x][y] = self.turn + 1

        self.turn ^= 1  # obrati hodnotu turn

    def dev_print(self):
        sada = [".", "O", "X"]
        for i in range(self.LENGTH):
            line = self.data[i]
            a = [sada[i] for i in line]
            print("".join(a))

    def is_full(self):
        for x in range(self.LENGTH):
            for y in range(self.LENGTH):
                if self.data[x][y] == 0:
                    return False
        return True

    def check_line(self, inp_line: list[int]) -> int:
        size = len(inp_line)
        line = inp_line + [0, 0]
        together = 0
        for i in range(size + 1):
            if together == 5 and line[i] != line[i - 1]:
                return line[i - 1]

            if i == 0 and line[i]:
                together = 1
            elif line[i]:
                if line[i - 1] == line[i]:
                    together += 1
                else:
                    together = 1
        return 0

    def is_over(self) -> int:
        """
        0: game is not over
        1: white won
        2: black won
        3: board is full, nobody won
        """

        if self.is_full():
            return 3
        ### TO FIX vvv !!!!!
        # diagonaly chceme jen s dostatencym poctem prvku - tj aspon 5
        for start in range(4, self.LENGTH):
            line = []
            x, y = start, 0
            while True:
                line.append(self.data[x][y])
                if y == start:
                    break
                y, x = y + 1, x - 1
            a = self.check_line(line)
            if a > 0:
                return a

        # DIAGONALS \
        for start in range(0, self.LENGTH - 4):  # nevim jestli -3 je spravne
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

        # COLLUMNS
        for i in range(self.LENGTH):
            line = [self.data[x][i] for x in range(self.LENGTH)]
            a = self.check_line(line)
            if a > 0:
                return a

        return 0

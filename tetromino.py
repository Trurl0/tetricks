
class Tetromino:

    TYPES = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']

    def __init__(self, body, letter):
        self.body   = body
        self.letter = letter

    @staticmethod
    def ITetromino(letter):
        return Tetromino(
            [
                [1, 1, 1, 1]
            ], letter
        )

    @staticmethod
    def OTetromino(letter):
        return Tetromino(
            [
                [1, 1],
                [1, 1]
            ], letter
        )

    @staticmethod
    def TTetromino(letter):
        return Tetromino(
            [
                [0, 1, 0],
                [1, 1, 1]
            ], letter
        )

    @staticmethod
    def STetromino(letter):
        return Tetromino(
            [
                [0, 1, 1],
                [1, 1, 0]
            ], letter
        )

    @staticmethod
    def ZTetromino(letter):
        return Tetromino(
            [
                [1, 1, 0],
                [0, 1, 1]
            ], letter
        )

    @staticmethod
    def JTetromino(letter):
        return Tetromino(
            [
                [1, 0, 0],
                [1, 1, 1]
            ], letter
        )

    @staticmethod
    def LTetromino(letter):
        return Tetromino(
            [
                [0, 0, 1],
                [1, 1, 1]
            ], letter
        )

    @staticmethod
    def create(letter):
        return getattr(Tetromino, '{}Tetromino'.format(letter.upper()))(letter)

    def __str__(self):
        return "\n".join(["".join(str(x)) for x in self.body])

    def copy(self):
        return Tetromino([row[:] for row in self.body], self.letter)

    def width(self):
        return len(self.body[0])

    def height(self):
        return len(self.body)

    def rotate_right(self):
        self.body = list(zip(*self.body[::-1]))
        return self

    def rotate_left(self):
        self.body = list(reversed(list(zip(*self.body))))
        return self

    def flip(self):
        self.body = [row[::-1] for row in self.body[::-1]]
        return self

from typing import *
import os

M: int = 8191  # Large enough prime (2^13 - 1)
A: int = 17    # Primitive modulo M


class Randomish:
    """
        Random-ish integer generator. Intended for use ONLY for aesthetic reasons. Quality of random numbers are
        acceptable to the naked eye and the generation algorithm is computationally cheap.
    """
    def __init__(self, y: Optional[int] = None, x: Optional[int] = None):
        self._y = y
        self._x = x
        self._next: int = 0  # To be initialised in the first seed
        self.seed(self._y, self._x)

    def seed(self, y: Optional[int] = None, x: Optional[int] = None):
        if y and x:
            self._y = y
            self._x = x
        else:
            self._y = int.from_bytes(os.urandom(13), 'big')
            self._x = int.from_bytes(os.urandom(13), 'big')

        # The first random integer should be co-prime to M and not 1 or 0
        self._next = max(pow(self._y, self._x, M), 2)

    def __iter__(self):
        return self

    def __next__(self):
        self._next = (A * self._next) % M
        return self._next

    def random(self):
        return next(self)

    def _randbelow(self, n: int):
        """Returns a random-ish number bellow the the given positive integer n"""
        return self.random() % n

    def randrange(self, start, stop):
        """Returns a random-ish number between start and stop inclusive of both endpoints"""
        diff = stop - start
        return start + self._randbelow(diff)

    def choice(self, seq: Sequence):
        """Returns a random-ish element from the given sequence"""
        idx: int = self._randbelow(len(seq))
        return seq[idx]


_inst = Randomish()
seed = _inst.seed
random = _inst.random
randrange = _inst.randrange
choice = _inst.choice

if __name__ == '__main__':
    rs = []
    for y in range(0, 10):
        for x in range(0, 10):
            seed(y, x)
            r = randrange(0, 10)
            print(r, end='')
        print('\n', end='')

from typing import *
import os

M: int = 127  # Large enough prime (2^13 - 1)
A: int = 3    # Primitive modulo M


class Randomish:
    """
        Random-ish integer generator. Intended for use ONLY for aesthetic reasons. Quality of random numbers are
        acceptable to the naked eye and the generation algorithm is computationally cheap.
    """
    def __init__(self, s: Optional[int] = None):
        self._hash_table = [122, 25, 27, 48, 115, 10, 12, 87, 65, 41, 54, 102, 89, 4, 34, 82, 36, 14, 116, 56, 72, 35, 44, 6, 105, 30, 29, 92, 67, 23, 94, 0, 59, 98, 70, 101, 17, 69, 110, 11, 111, 47, 40, 85, 64, 71, 95, 126, 117, 125, 75, 21, 62, 61, 32, 120, 90, 106, 1, 5, 7, 81, 86, 79, 57, 9, 107, 19, 93, 77, 38, 31, 26, 42, 97, 52, 76, 103, 74, 49, 100, 78, 112, 43, 3, 20, 39, 84, 66, 50, 88, 83, 124, 13, 108, 109, 33, 123, 91, 60, 15, 127, 119, 28, 58, 8, 51, 46, 2, 55, 114, 113, 45, 80, 73, 104, 118, 22, 53, 37, 63, 99, 121, 68, 16, 96, 24, 18]

        self._next = 0
        self.seed(s)

    def seed(self, s: Optional[int] = None):
        if s is None:
            s = int.from_bytes(os.urandom(16), 'big')
        self._next = s % M

    def fast_hash(self, y: int, x: int) -> int:
        """Pearson hashing."""
        message: str = f"{x}{y}"
        hash = len(message) % 128
        for i in message:
            hash = self._hash_table[hash ^ ord(i)]

        return hash

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
fast_hash = _inst.fast_hash
random = _inst.random
randrange = _inst.randrange
choice = _inst.choice

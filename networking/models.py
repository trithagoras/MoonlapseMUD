import random
import sys
from typing import *
import traceback

class Player:
    def __init__(self):
        self._username: Optional[str] = None
        self._id: Optional[int] = None
        self._char: Optional[chr] = None
        self._position: Optional[List[int, int]] = None

    def assign_id(self, player_id) -> None:
        self._id = player_id

        choices: List[chr] = ['#', '@', '&', '+', '%', '$', '£']
        self._char: chr = choices[self._id]
        if self._id + 1 > len(choices):
            self._char = 65 + self._id - len(choices)

    def assign_location(self, position: List[int], room) -> None:
        self._position = position
        if self._position == (None, None):
            while True:
                self._position = [random.randint(1, room.height), random.randint(1, room.width)]
                if self._position not in room.walls:
                    break

    def assign_username(self, username: str) -> None:
        self._username = username

    def get_username(self) -> str:
        return self._username

    def get_id(self) -> int:
        return self._id

    def get_position(self) -> Tuple[int]:
        return self._position

    def move(self, direction: chr):
        if direction == 'u':
            self._position[0] -= 1
        elif direction == 'd':
            self._position[0] += 1
        elif direction == 'l':
            self._position[1] -= 1
        else:
            self._position[1] += 1
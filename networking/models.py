import random
import sys
from typing import *
import traceback

class Player:
    def __init__(self):
        self._username: Optional[str] = None
        self._id: Optional[int] = None
        self._char: Optional[chr] = None
        self._position: Optional[List[int]] = None

    def assign_id(self, player_id) -> None:
        self._id = player_id

        choices: List[chr] = ['#', '@', '&', '+', '%', '$', '£']
        self._char: chr = choices[self._id]
        if self._id + 1 > len(choices):
            self._char = 65 + self._id - len(choices)

    def assign_location(self, position: List[int], room) -> None:
        if position == [None, None]:
            while True:
                self._position = [random.randint(1, room.height), random.randint(1, room.width)]
                if self._position not in room.walls:
                    break
        else:
            self._position = [position[0], position[1]]

    def assign_username(self, username: str) -> None:
        self._username = username

    def get_username(self) -> str:
        return self._username

    def get_id(self) -> int:
        return self._id

    def get_position(self) -> Tuple[int]:
        return tuple(self._position)

    def set_position(self, destination: List[int]) -> None:
        self._position = destination
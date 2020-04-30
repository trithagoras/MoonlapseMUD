import random
import sys
from typing import *
import traceback

class Player:
    def __init__(self, player_id):
        self._username: Optional[str] = None
        self._position: Optional[List[int]] = None

        self._id: Optional[int] = None
        self._char: Optional[chr] = None
        self._assign_id(player_id)

    def ready(self) -> bool:
        return None not in (self._username, self._position, self._id, self._char)

    def _assign_id(self, player_id) -> None:
        self._id = player_id

        choices: List[chr] = ['#', '@', '&', '+', '%', '$', '£']
        if self._id > len(choices) - 1:
            self._char = 65 + self._id - len(choices)
        else:
            self._char: chr = choices[self._id]

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
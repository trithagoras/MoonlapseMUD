import random
from typing import *


class Player:
    def __init__(self, player_id: int):
        self._id: int = player_id

        self._username: Optional[str] = None
        self._position: Optional[List[int]] = None
        self._char: Optional[chr] = None

    def ready(self) -> bool:
        return None not in (self._username, self._position, self._id, self._char)

    def _assign_id(self, player_id) -> None:
        self._id = player_id

        choices: List[chr] = ['#', '@', '&', '+', '%', '$', '£']
        if self._id > len(choices) - 1:
            self._char = 65 + self._id - len(choices)
        else:
            self._char: chr = choices[self._id]

    def assign_location(self, position: List[int], walls: List[List[int]], max_height: int, max_width: int) -> None:
        if position == [None, None]:
            while True:
                self._position = [random.randint(1, max_height), random.randint(1, max_width)]
                if self._position not in walls:
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

    def get_char(self) -> chr:
        return self._char

    def __repr__(self):
        return f"Player: [username={self.get_username()}, id={self.get_id()}]"

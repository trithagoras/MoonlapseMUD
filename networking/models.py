import random
from typing import *
import copy


class Player:
    def __init__(self, player_id: int):
        self._id: int = player_id
        self._username: Optional[str] = None
        self._position: Optional[List[int]] = None
        self._char: Optional[chr] = None
        self._view_radius: Optional[int] = None

    def ready(self) -> bool:
        return None not in (self._username, self._position, self._id, self._char)

    def _assign_id(self, player_id) -> None:
        self._id = player_id

        choices: List[chr] = ['#', '@', '&', '+', '%', '$', '£']
        if self._id > len(choices) - 1:
            self._char = 65 + self._id - len(choices)
        else:
            self._char: chr = choices[self._id]

    def assign_location(self, position: List[int], walls: List[Tuple[int, int]], max_height: int, max_width: int) -> None:
        if position == [None, None]:
            while True:
                self._position = [random.randint(1, max_height), random.randint(1, max_width)]
                if tuple(self._position) not in walls:
                    break
        else:
            self._position = [position[0], position[1]]

    def assign_username(self, username: str) -> None:
        self._username = username

    def get_username(self) -> str:
        return self._username

    def get_id(self) -> int:
        return self._id

    def get_position(self) -> Tuple[int, int]:
        return tuple(self._position)

    def set_position(self, destination: List[int]) -> None:
        self._position = destination

    def get_char(self) -> chr:
        return self._char

    def set_view_radius(self, sight_radius: int) -> None:
        self._view_radius = sight_radius

    def get_view_radius(self) -> int:
        return self._view_radius

    def get_view_range_topleft(self) -> Tuple[int, int]:
        pos = self.get_position()
        r = self.get_view_radius()
        return pos[0] - r - 1, pos[1] - r - 1

    def get_view_range_botright(self) -> Tuple[int, int]:
        pos = self.get_position()
        r = self.get_view_radius()
        return pos[0] + r + 1, pos[1] + r + 1

    def __hash__(self) -> int:
        return hash((self.get_position(), self.get_id()))

    def __eq__(self, o: object) -> bool:
        return isinstance(o, Player) and hash(o) == hash(self)

    def __repr__(self):
        return f"Player: [username={self.get_username()}, id={self.get_id()}]"

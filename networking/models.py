import random
from typing import *
from maps import Room


class Player:
    def __init__(self, username: str):
        self._username: str = username
        self._position: Optional[Tuple[int, int]] = None
        self._room: Optional[Room] = None
        self._char: chr = '@'
        self._view_radius: Optional[int] = None

    def ready(self) -> bool:
        return None not in (self._username, self._position, self._char)

    def assign_location(self, position: Tuple[Optional[int], Optional[int]]) -> None:
        if not self.get_room():
            raise ValueError("Cannot assign location without a room. Must set the room first.")

        room = self.get_room()
        if position == (None, None):
            room.unpack()
            while True:
                self._position = random.randint(1, room.height), random.randint(1, room.width)
                if self._position not in room.solidmap.values():
                    room.pack()
                    break
        else:
            self._position = (position[0], position[1])

    def get_username(self) -> str:
        return self._username

    def get_position(self) -> Tuple[int, int]:
        return self._position

    def set_position(self, destination: List[int]) -> None:
        self._position = destination

    def get_room(self) -> Room:
        return self._room

    def set_room(self, room: Room) -> None:
        self._room = room

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
        return hash(self.get_username())

    def __eq__(self, o: object) -> bool:
        return isinstance(o, Player) and hash(o) == hash(self)

    def __repr__(self):
        return f"Player {self.get_username()}"

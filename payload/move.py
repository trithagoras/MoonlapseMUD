from enum import Enum


class Direction(str, Enum):
    UP: str = "up"
    RIGHT: str = "right"
    DOWN: str = "down"
    LEFT: str = "left"

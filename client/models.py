class User:
    def __init__(self, username: str):
        self.username: str = username


class Room:
    def __init__(self, name: str, path: str):
        self.name: str = name
        self.path: str = path


class Entity:
    def __init__(self, room: Room, y: int, x: int, char: chr = '@'):
        self.room: Room = room
        self.y: int = y
        self.x: int = x
        self.char: chr = char


class Player:
    def __init__(self, user: User, entity: Entity, view_radius: int = 10):
        self.user: User = user
        self.entity: Entity = entity
        self.view_radius: int = view_radius

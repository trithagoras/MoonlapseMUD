class Model:
    def __init__(self, attr: dict):
        for k, v in attr.items():
            setattr(self, k, v)


class User(Model):
    def __init__(self, attr: dict):
        super().__init__()


class Room(Model):
    def __init__(self, attr: dict):
        super().__init__()


class Entity(Model):
    def __init__(self, attr: dict):
        super().__init__()


class Player(Model):
    def __init__(self, attr: dict):
        super().__init__()

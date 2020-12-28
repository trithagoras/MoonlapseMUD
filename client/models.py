class Model:
    def __init__(self, attr: dict):
        for k, v in attr.items():
            setattr(self, k, v)

    def update(self, delta: dict):
        if delta['id'] != self.id:
            raise ValueError("Cannot change model's ID")
        for k, v in delta.items():
            setattr(self, k, v)


class User(Model):
    def __init__(self, attr: dict):
        super().__init__(attr)


class Room(Model):
    def __init__(self, attr: dict):
        super().__init__(attr)


class Entity(Model):
    def __init__(self, attr: dict):
        super().__init__(attr)


class Player(Model):
    def __init__(self, attr: dict):
        super().__init__(attr)


class Portal(Model):
    def __init__(self, attr: dict):
        super().__init__(attr)
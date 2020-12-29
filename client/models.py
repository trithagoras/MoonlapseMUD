class Model:
    def __init__(self, attr: dict):
        self.id = 0
        for k, v in attr.items():
            setattr(self, k, v)

    def update(self, delta: dict):
        if delta['id'] != self.id:
            raise ValueError("Cannot change model's ID")
        for k, v in delta.items():
            setattr(self, k, v)


class User(Model):
    def __init__(self, attr: dict):
        self.username = ""
        super().__init__(attr)


class Room(Model):
    def __init__(self, attr: dict):
        self.name = ""
        self.file_name = ""
        super().__init__(attr)


class Entity(Model):
    def __init__(self, attr: dict):
        self.name = ""
        self.typename = ""
        super().__init__(attr)


class Item(Model):
    def __init__(self, attr: dict):
        self.entity_id = 0
        self.value = 0
        super().__init__(attr)


class Player(Model):
    def __init__(self, attr: dict):
        self.user_id = 0
        self.entity_id = 0
        self.inventory_id = 0
        super().__init__(attr)


class Portal(Model):
    def __init__(self, attr: dict):
        self.entity_id = 0
        self.linkedy = 0
        self.linkedx = 0
        self.linkedroom_id = 0
        super().__init__(attr)


class InstancedEntity(Model):
    def __init__(self, attr: dict):
        self.entity_id = 0
        self.y = 0
        self.x = 0
        self.room_id = 0
        self.amount = 0
        super().__init__(attr)


class Container(Model):
    def __init__(self, attr: dict):
        super().__init__(attr)


class ContainerItem(Model):
    def __init__(self, attr: dict):
        self.container_id = 0
        self.item_id = 0
        self.amount = 0
        super().__init__(attr)

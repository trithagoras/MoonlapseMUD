import curses

import maps
from client.controllers.controller import Controller
from client.views.gameview import GameView
from networking import packet
from networking.logger import Log
from client.controllers.widgets import TextField


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

    def __getitem__(self, item):
        return self.__dict__[item]


class State:
    NORMAL = 0
    LOGOUT = 1
    MOVE_ROOMS = 2


class Game(Controller):
    def __init__(self, cs):
        super().__init__(cs)
        self.chatbox = TextField(self, title="Say: ", max_length=80)

        self.visible_instances = set()
        self.player_info = None  # id, entity, inventory
        self.player_instance = None  # id, entity, room_id, y, x
        self.inventory = {}     # item.id : {id, item, amount}
        self.room = None

        self.state = State.NORMAL

        self.weather = "Clear"

        self.logger = Log()

        self.view = GameView(self)

    def ready(self):
        return False not in [bool(data) for data in (self.player_info, self.player_instance, self.room)]

    def process_packet(self, p) -> bool:
        if isinstance(p, packet.ServerModelPacket):
            if p.payloads[0].value == 'ContainerItem':
                self.process_model(p.payloads[0].value, p.payloads[1].value)
            elif not self.ready():
                self.initialise_my_models(p.payloads[0].value, p.payloads[1].value)
            else:
                self.process_model(p.payloads[0].value, p.payloads[1].value)

        elif isinstance(p, packet.GoodbyePacket):
            # Some instance has been removed from room (item picked up, player logged out, etc.)
            entityid: int = p.payloads[0].value
            departed = next((e for e in self.visible_instances if e['id'] == entityid), None)
            if departed:
                self.visible_instances.remove(departed)

        elif isinstance(p, packet.WeatherChangePacket):
            self.weather = p.payloads[0].value

        elif isinstance(p, packet.MoveRoomsPacket):
            self.state = State.MOVE_ROOMS

        elif isinstance(p, packet.ServerLogPacket):
            self.logger.log(p.payloads[0].value)

        elif isinstance(p, packet.OkPacket):
            if self.state == State.LOGOUT:
                self.cs.change_controller("MainMenu")
            elif self.state == State.MOVE_ROOMS:
                self.reinitialize()
                self.state = State.NORMAL
            else:
                pass
        elif isinstance(p, packet.DenyPacket):
            pass
        elif isinstance(p, packet.ServerTickRatePacket):
            pass

        else:
            return False

        return True

    def initialise_my_models(self, mtype: str, data: dict):
        if mtype == 'Room':
            self.room = maps.Room(data['id'], data['name'], data['file_name'])
        elif mtype == 'Instance':
            self.player_instance = Model(data)
        elif mtype == 'Player':
            self.player_info = Model(data)

    def process_model(self, mtype: str, data: dict):
        if mtype == 'Instance':
            instance = Model(data)
            visible_instance = next((e for e in self.visible_instances if e['id'] == instance['id']), None)
            if visible_instance:  # If the incoming entity is already visible to us, update it
                visible_instance.update(data)
                # If the incoming entity is ours, update it
                if instance.id == self.player_instance['id']:
                    self.player_instance.update(data)
            else:  # If not visible already, add to visible list (it is only ever sent to us if it's in view)
                self.visible_instances.add(instance)

        elif mtype == 'ContainerItem':
            ci = Model(data)
            itemid = ci['item']['id']
            self.inventory[itemid] = ci

    def process_input(self, key: int):
        if self.chatbox.selected:
            if key == ord('\n'):
                self.send_chat(self.chatbox.value)
                self.chatbox.value = ""
                self.chatbox.cursor = 0
            self.chatbox.process_input(key)
            return

        if key == ord('q'):
            self.cs.ns.send_packet(packet.LogoutPacket(self.cs.ns.username))
            self.state = State.LOGOUT
        elif key == curses.KEY_UP:
            self.cs.ns.send_packet(packet.MoveUpPacket())
        elif key == curses.KEY_DOWN:
            self.cs.ns.send_packet(packet.MoveDownPacket())
        elif key == curses.KEY_LEFT:
            self.cs.ns.send_packet(packet.MoveLeftPacket())
        elif key == curses.KEY_RIGHT:
            self.cs.ns.send_packet(packet.MoveRightPacket())
        elif key == ord('g'):
            self.cs.ns.send_packet(packet.GrabItemPacket())
        elif key == ord('\n'):
            self.chatbox.select()
        pass

    def send_chat(self, message):
        self.cs.ns.send_packet(packet.ChatPacket(message))

    def reinitialize(self):
        self.room = None
        self.player_instance = None
        self.visible_instances = set()

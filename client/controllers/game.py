import curses
import curses.ascii

import maps
from client.controllers.controller import Controller
from client.views.gameview import GameView
from networking import packet
from networking.logger import Log
from client.controllers.widgets import TextField
from client.controllers import keybindings


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


class Context:
    NORMAL = 0
    LOGOUT = 1
    MOVE_ROOMS = 2


class State:
    NORMAL = 0
    LOOKING = 1
    GRABBING_ITEM = 2


class Game(Controller):
    def __init__(self, cs):
        super().__init__(cs)
        self.chatbox = TextField(self, title="Say: ", max_length=80)

        self.visible_instances = set()
        self.player_info = None  # id, entity, inventory
        self.player_instance = None  # id, entity, room_id, y, x
        self.inventory = {}     # item.id : {id, item, amount}
        self.room = None

        self.context = Context.NORMAL
        self.state = State.NORMAL

        self.look_cursor_y = 0
        self.look_cursor_x = 0

        self.weather = "Clear"

        self.logger = Log()
        self.quicklog = ""      # line that appears above win1

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
            self.context = Context.MOVE_ROOMS

        elif isinstance(p, packet.ServerLogPacket):
            self.logger.log(p.payloads[0].value)

        elif isinstance(p, packet.OkPacket):
            if self.context == Context.LOGOUT:
                self.cs.change_controller("MainMenu")
            elif self.context == Context.MOVE_ROOMS:
                self.reinitialize()
                self.context = Context.NORMAL
            else:
                pass
        elif isinstance(p, packet.DenyPacket):
            if self.state == State.GRABBING_ITEM:
                self.quicklog = p.payloads[0].value
                self.state = State.NORMAL
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

            amt = ci['amount']
            if itemid in self.inventory:
                amt -= self.inventory[itemid]['amount']

            if self.state == State.GRABBING_ITEM:
                self.quicklog = f"You pick up {amt} {ci['item']['entity']['name']}."
                self.state = State.NORMAL

            self.inventory[itemid] = ci

    def update(self):
        if self.state == State.LOOKING:
            cpos = self.look_cursor_y, self.look_cursor_x
            for instance in self.visible_instances:
                pos = instance['y'], instance['x']
                if cpos == pos:
                    self.quicklog = instance['entity']['name']
                    return
            self.quicklog = ""

    def process_input(self, key: int):
        super().process_input(key)
        
        if self.process_global_input(key):
            return

        # input state machine
        if self.state == State.NORMAL:
            self.process_normal_input(key)
        elif self.state == State.LOOKING:
            self.process_look_input(key)

    def process_global_input(self, key: int) -> bool:
        if self.chatbox.selected:
            if keybindings.enter(key):
                self.send_chat(self.chatbox.value)
                self.chatbox.value = ""
                self.chatbox.cursor = 0
                self.view.chat_scroll = 0
            self.chatbox.process_input(key)
            return True
        elif keybindings.enter(key):
            self.chatbox.select()
        elif key == ord('q'):
            self.cs.ns.send_packet(packet.LogoutPacket(self.cs.ns.username))
            self.context = Context.LOGOUT
        elif key == ord('k'):
            self.quicklog = ""

            if self.state != State.LOOKING:
                self.state = State.LOOKING
                self.look_cursor_y = self.player_instance['y']
                self.look_cursor_x = self.player_instance['x']
            else:
                self.state = State.NORMAL

        elif key == ord('1'):
            self.view.focused_win = self.view.win1
        elif key == ord('2'):
            self.view.focused_win = self.view.win2
        elif key == ord('3'):
            self.view.focused_win = self.view.win3

        elif self.view.focused_win == self.view.win3:
            if key == curses.KEY_DOWN and self.view.chat_scroll > 0:
                self.view.chat_scroll -= 1
            elif key == curses.KEY_UP and self.view.chat_scroll < self.view.times_logged - self.view.win3.height + self.view.chatwin.height:
                self.view.chat_scroll += 1

        else:
            return False
        return True

    def process_normal_input(self, key: int) -> bool:
        if key == curses.KEY_UP:
            self.move(-1, 0)
            self.cs.ns.send_packet(packet.MoveUpPacket())
        elif key == curses.KEY_DOWN:
            self.move(1, 0)
            self.cs.ns.send_packet(packet.MoveDownPacket())
        elif key == curses.KEY_LEFT:
            self.move(0, -1)
            self.cs.ns.send_packet(packet.MoveLeftPacket())
        elif key == curses.KEY_RIGHT:
            self.move(0, 1)
            self.cs.ns.send_packet(packet.MoveRightPacket())
        elif key == ord('g'):
            self.state = State.GRABBING_ITEM
            self.cs.ns.send_packet(packet.GrabItemPacket())
        else:
            return False
        return True

    def move(self, dy, dx):
        if not self.player_instance:
            # We are most likely loading the room, OK to ignore
            return
        y: int = self.player_instance['y']
        x: int = self.player_instance['x']
        dest_y: int = y + dy
        dest_x: int = x + dx

        if self.room.coordinate_exists(dest_y, dest_x) and self.room.at('solid', dest_y, dest_x) == maps.NOTHING:
            self.player_instance.update({
                'id': self.player_instance['id'],
                'y': dest_y,
                'x': dest_x
            })

    def process_look_input(self, key: int) -> bool:
        desired_y = self.look_cursor_y
        desired_x = self.look_cursor_x

        if key == curses.KEY_UP:
            desired_y -= 1
            pass
        elif key == curses.KEY_DOWN:
            desired_y += 1
        elif key == curses.KEY_LEFT:
            desired_x -= 1
        elif key == curses.KEY_RIGHT:
            desired_x += 1
        else:
            return False

        y, x = self.player_instance['y'], self.player_instance['x']
        if self.room.coordinate_exists(desired_y, desired_x):
            if abs(desired_y - y) <= 10 and abs(desired_x - x) <= 10:
                self.look_cursor_y = desired_y
                self.look_cursor_x = desired_x

        return True

    def send_chat(self, message):
        self.cs.ns.send_packet(packet.ChatPacket(message))

    def reinitialize(self):
        self.room = None
        self.player_instance = None
        self.visible_instances = set()

import curses
import curses.ascii
import threading
import time
import models
import maps
from enum import Enum
from typing import *
from networking import packet
from networking.logger import Log
from .controller import Controller
from ..views.gameview import GameView
from client.utils import NetworkState


class Action(Enum):
    MOVE_ROOMS = 1
    LOGOUT = 2


class Game(Controller):
    def __init__(self, ns: NetworkState):
        super().__init__()
        self.ns = ns

        self.action: Optional[Action] = None

        # Game data
        self.room: Optional[models.Room] = None
        self.instance: Optional[models.InstancedEntity] = None
        self.player: Optional[models.Player] = None

        self.visible_instances: Set[models.InstancedEntity] = set()
        self.inventory = {}     # item_id : ContainerItem
        self.tick_rate: Optional[int] = None

        self.logger: Log = Log()

        self.weather = "Clear"

        # UI
        self.chatbox = None
        self.view = GameView(self)

        self._logged_in = True

    def start(self) -> None:
        # Listen for game data in its own thread
        threading.Thread(target=self.receive_data).start()

        # Don't draw with game data until it's been received
        while not self.ready():
            time.sleep(0.2)

        # Start the view's display loop
        super().start()

    def receive_data(self) -> None:
        while self._logged_in:
            try:
                # Get initial room data if not already done
                while not self.ready() and self._logged_in:
                    p = self.ns.receive_packet()
                    if isinstance(p, packet.ServerModelPacket):
                        self.initialise_models(p.payloads[0].value, p.payloads[1].value)
                    elif isinstance(p, packet.ServerTickRatePacket):
                        self.tick_rate = p.payloads[0].value

                # Get volatile data such as player positions, etc.
                p = self.ns.receive_packet()

                if isinstance(p, packet.ServerModelPacket):
                    type: str = p.payloads[0].value
                    model: dict = p.payloads[1].value

                    if type == 'Instance':
                        instance = models.InstancedEntity(model)
                        visible_instance = next((e for e in self.visible_instances if e.id == instance.id), None)
                        if visible_instance:  # If the incoming entity is already visible to us, update it
                            visible_instance.update(model)
                            # If the incoming entity is ours, update it
                            if instance.id == self.instance.id:
                                self.instance.update(model)
                        else:  # If it's not visible to us already, add it to the visible list (it is only ever sent to us if it's in view)
                            self.visible_instances.add(instance)

                    elif type == 'ContainerItem':
                        # this type is only sent when player picks up an item to inventory
                        # this only assumes that no items have state. e.g. no durability; allowing stacking
                        ci = models.ContainerItem(model)
                        self.inventory[ci.item["id"]] = ci

                elif isinstance(p, packet.ServerLogPacket):
                    self.logger.log(p.payloads[0].value)

                # Another player has logged out, left the room, or disconnected so we remove them from the game.
                elif isinstance(p, packet.GoodbyePacket):
                    entityid: int = p.payloads[0].value
                    departed: models.InstancedEntity = next((e for e in self.visible_instances if e.id == entityid), None)
                    if departed:
                        self.visible_instances.remove(departed)

                elif isinstance(p, packet.MoveRoomsPacket):
                    self.action = Action.MOVE_ROOMS

                elif isinstance(p, packet.WeatherChangePacket):
                    self.weather = p.payloads[0].value

                elif isinstance(p, packet.OkPacket):
                    if self.action == Action.MOVE_ROOMS:
                        self.action = None
                        self.reinitialize()
                    elif self.action == Action.LOGOUT:
                        self.action = None
                        self.stop()
                        break

                elif isinstance(p, packet.DenyPacket):
                    pass
                    # Define custom followup behaviours here, e.g.
                    # if self.action == Action.DO_THIS:
                    #   self.action = None
                    #   self.action = do_that()

            except Exception as e:
                self.logger.log(str(e))

        # The loop ended?
        self.logger.log("Seems you've stopped listening friend...")

    def initialise_models(self, type: str, data: dict):
        if type == 'Room':
            # if not self._client_has_map_layout(data):
            #     self._add_map_layout(data)

            self.room = maps.Room(data['id'], data['name'], data['file_name'])

        elif type == 'Instance':
            self.instance = models.InstancedEntity(data)

        elif type == 'Player':
            self.player = models.Player(data)

    # def _client_has_map_layout(self, data: dict) -> bool:
    #     for expected_attr in 'name', 'ground_data', 'solid_data', 'roof_data', 'height', 'width':
    #         if expected_attr not in data:
    #             raise KeyError("Model dict invalid for room")
    #
    #     roomname = data['name']
    #     roompath = os.path.join(os.path.dirname(os.path.realpath(maps.__file__)), "layouts", roomname)
    #
    #     if not os.path.exists(roompath) or not os.path.isdir(roompath):
    #         return False
    #
    #     for dtype in "ground", "solid", "roof":
    #         dpath = os.path.join(roompath, f"{dtype}.data")
    #         if not os.path.exists(dpath) or not os.path.isfile(dpath):
    #             return False
    #
    #     return True
    #
    # def _add_map_layout(self, data: dict):
    #     roomname: str = data['name']
    #     roompath = os.path.join(os.path.dirname(os.path.realpath(maps.__file__)), "layouts", roomname)
    #     try:
    #         os.makedirs(roompath)
    #     except FileExistsError:
    #         pass
    #
    #     for dtype in "ground", "solid", "roof":
    #         with open(os.path.join(roompath, f"{dtype}.data"), 'w') as f:
    #             f.writelines('\n'.join(data[f"{dtype}_data"]))

    def handle_input(self) -> int:
        key = super().handle_input()

        # Movement
        directionpacket: Optional[packet.MovePacket] = None
        if key == curses.KEY_UP:
            directionpacket = packet.MoveUpPacket()
        elif key == curses.KEY_RIGHT:
            directionpacket = packet.MoveRightPacket()
        elif key == curses.KEY_DOWN:
            directionpacket = packet.MoveDownPacket()
        elif key == curses.KEY_LEFT:
            directionpacket = packet.MoveLeftPacket()

        elif key == ord('g'):
            self.ns.send_packet(packet.GrabItemPacket())

        # todo: this is a debug: dropping should be handled in inventory
        # elif key == ord('d'):
        #     for key in self.inventory:
        #         self.ns.send_packet(packet.DropItemPacket(key))

        # Changing window focus
        elif key in (ord('1'), ord('2'), ord('3')):
            self.view.focus = int(chr(key))

        # Changing window 2 focus
        elif key == ord('?'):
            self.view.win2_focus = GameView.Window2Focus.HELP
        elif key == ord('k'):
            self.view.win2_focus = GameView.Window2Focus.SKILLS
        elif key == ord('i'):
            self.view.win2_focus = GameView.Window2Focus.INVENTORY
        elif key == ord('p'):
            self.view.win2_focus = GameView.Window2Focus.SPELLBOOK
        elif key == ord('g'):
            self.view.win2_focus = GameView.Window2Focus.GUILD
        elif key == ord('j'):
            self.view.win2_focus = GameView.Window2Focus.JOURNAL

        # Chat
        elif key in (curses.KEY_ENTER, curses.ascii.LF, curses.ascii.CR):
            self.view.chatbox.modal()
            self.chat(self.view.chatbox.value)

        # Quit on Windows. TODO: Figure out how to make CTRL+C or ESC work.
        elif key == ord('q'):
            self.ns.send_packet(packet.LogoutPacket(self.ns.username))
            self.action = Action.LOGOUT

        if directionpacket:
            self.ns.send_packet(directionpacket)

        return key

    def chat(self, message: str) -> None:
        self.ns.send_packet(packet.ChatPacket(message))
        self.view.chatbox.value = ''

    def ready(self) -> bool:
        return False not in [bool(data) for data in (self.instance, self.player, self.room, self.tick_rate)]

    def reinitialize(self):
        self.instance = None
        self.visible_instances = set()
        self.tick_rate = None

    def stop(self) -> None:
        self._logged_in = False
        super().stop()

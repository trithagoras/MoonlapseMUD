import curses
import curses.ascii
import os
import socket
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


class Action(Enum):
    MOVE_ROOMS = 1
    LOGOUT = 2


class Game(Controller):
    def __init__(self, s: socket.socket, username: str):
        super().__init__()
        self.s: socket.socket = s
        self.action: Optional[Action] = None

        # Game data
        self.user: Optional[models.User] = None
        self.room: Optional[models.Room] = None
        self.entity: Optional[models.Entity] = None
        self.player: Optional[models.Player] = None

        self.visible_entities: Set[models.Entity] = set()
        self.tick_rate: Optional[int] = None

        self.logger: Log = Log()

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
                    p: packet.Packet = packet.receive(self.s)
                    if isinstance(p, packet.ServerModelPacket):
                        self.initialise_models(p.payloads[0].value, p.payloads[1].value)
                    elif isinstance(p, packet.ServerTickRatePacket):
                        self.tick_rate = p.payloads[0].value

                # Get volatile data such as player positions, etc.
                p: packet.Packet = packet.receive(self.s)

                if isinstance(p, packet.ServerModelPacket):
                    type: str = p.payloads[0].value
                    model: dict = p.payloads[1].value

                    if type == 'Entity':
                        # If the incoming entity is our player, update it
                        entity = models.Entity(model)
                        if entity.id == self.entity.id:
                            self.entity = entity

                        # If the incoming entity is already visible to us, update it
                        for e in self.visible_entities:
                            if e.id == entity.id:
                                self.visible_entities.remove(e)
                                self.visible_entities.add(entity)

                        # Else, add it to the visible list (it is only ever sent to us if it's in view)
                        self.visible_entities.add(entity)

                elif isinstance(p, packet.ServerLogPacket):
                    self.logger.log(p.payloads[0].value)

                # Another player has logged out, left the room, or disconnected so we remove them from the game.
                elif isinstance(p, packet.GoodbyePacket):
                    entityid: int = p.payloads[0].value
                    departed: models.Entity = next((e for e in self.visible_entities if e.id == entityid), None)
                    if departed:
                        self.visible_entities.remove(departed)

                if isinstance(p, packet.MoveRoomsPacket):
                    self.action = Action.MOVE_ROOMS

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
        if type == 'User':
            self.user = models.User(data)

        elif type == 'Room':
            if not self._client_has_map_layout(data):
                self._add_map_layout(data)

            self.room = maps.Room(data['name'])
            if not self.room.is_unpacked():
                self.room.unpack()

        elif type == 'Entity':
            self.entity = models.Entity(data)

        elif type == 'Player':
            self.player = models.Player(data)

    def _client_has_map_layout(self, data: dict) -> bool:
        for expected_attr in 'name', 'ground_data', 'solid_data', 'roof_data', 'height', 'width':
            if expected_attr not in data:
                raise KeyError("Model dict invalid for room")

        roomname = data['name']
        roompath = os.path.join("maps", "layouts", roomname)

        if not os.path.exists(roompath) or not os.path.isdir(roompath):
            return False

        for dtype in "ground", "solid", "roof":
            dpath = os.path.join(roompath, f"{dtype}.data")
            if not os.path.exists(dpath) or not os.path.isfile(dpath):
                return False

        return True

    def _add_map_layout(self, data: dict):
        roomname: str = data['name']
        layoutpath: str = os.path.join("maps", "layouts", roomname)
        try:
            os.makedirs(layoutpath)
        except FileExistsError:
            pass

        for dtype in "ground", "solid", "roof":
            with open(os.path.join(layoutpath, f"{dtype}.data"), 'w') as f:
                f.writelines('\n'.join(data[f"{dtype}_data"]))

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

        if directionpacket:
            packet.send(directionpacket, self.s)

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
            packet.send(packet.LogoutPacket(self.user.username), self.s)
            self.action = Action.LOGOUT

        return key

    def chat(self, message: str) -> None:
        packet.send(packet.ChatPacket(message), self.s)

    def ready(self) -> bool:
        return False not in [bool(data) for data in (self.user, self.entity, self.player, self.room, self.tick_rate)]

    def reinitialize(self):
        self.entity = None
        self.visible_entities = set()
        self.tick_rate = None

    def stop(self) -> None:
        self._logged_in = False
        super().stop()

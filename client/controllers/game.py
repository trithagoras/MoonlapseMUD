import curses
import curses.ascii
import socket
import threading
import time
from enum import Enum
from typing import *
from networking import packet
from networking import models
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
        self.username = username
        self.action: Optional[Action] = None

        # Game data
        self.player: Optional[models.Player] = None
        self.visible_users: Dict[str, Tuple[int, int]] = {}
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
            # Get initial room data if not already done
            while not self.ready() and self._logged_in:
                p: packet.Packet = packet.receive(self.s)
                if isinstance(p, packet.ServerPlayerPacket):
                    self.player = p.payloads[0].value
                    self.player.get_room().unpack()
                elif isinstance(p, packet.ServerEntityPositionPacket):
                    self.user_exchange(p.payloads[0].value, p.payloads[1].value)
                elif isinstance(p, packet.ServerTickRatePacket):
                    self.tick_rate = p.payloads[0].value

                ready = self.ready()

            # Get volatile data such as player positions, etc.
            p: packet.Packet = packet.receive(self.s)

            if isinstance(p, packet.ServerEntityPositionPacket):
                self.user_exchange(p.payloads[0].value, tuple(p.payloads[1].value))  # Can't receive tuples as JSON

            elif isinstance(p, packet.ServerLogPacket):
                self.logger.log(p.payloads[0].value)

            # Another player has logged out, left the room, or disconnected so we remove them from the game.
            elif isinstance(p, packet.LogoutPacket) or isinstance(p, packet.GoodbyePacket):
                username: str = p.payloads[0].value
                if username in self.visible_users:
                    self.visible_users.pop(username)

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

    def user_exchange(self, username: str, position: Tuple[int, int]):
        # If the received username is ourselves, update ourself
        if username == self.username:
            self.player.set_position(list(position))

        # If the received player is somebody else, either update the other user position or add a new one in
        self.visible_users[username] = position

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

        # TODO: Remove this
        # Moving rooms (just a test)
        elif key == ord('f'):
            self.action = Action.MOVE_ROOMS
            packet.send(packet.MoveRoomsPacket('forest'), self.s)
        elif key == ord('t'):
            self.action = Action.MOVE_ROOMS
            packet.send(packet.MoveRoomsPacket('tavern'), self.s)


        # Chat
        elif key in (curses.KEY_ENTER, curses.ascii.LF, curses.ascii.CR):
            self.view.chatbox.modal()
            self.chat(self.view.chatbox.value)

        # Quit on Windows. TODO: Figure out how to make CTRL+C or ESC work.
        elif key == ord('q'):
            packet.send(packet.LogoutPacket(self.player.get_username()), self.s)
            self.action = Action.LOGOUT

        return key

    def chat(self, message: str) -> None:
        packet.send(packet.ChatPacket(message), self.s)

    def ready(self) -> bool:
        return False not in [bool(data) for data in (self.player, self.tick_rate)] and self.player.get_room().is_unpacked()

    def reinitialize(self):
        self.player = None
        self.visible_users = {}
        self.tick_rate = None

    def stop(self) -> None:
        self._logged_in = False
        super().stop()

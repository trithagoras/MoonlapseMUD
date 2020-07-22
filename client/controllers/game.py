import curses
import curses.ascii
import socket
import threading
import time
import maps
from typing import *
from networking import packet
from networking import models
from networking.logger import Log
from .controller import Controller
from ..views.gameview import GameView


class Game(Controller):
    def __init__(self, s: socket.socket):
        super().__init__()
        self.s: socket.socket = s

        # Game data
        self.player: Optional[models.Player] = None
        self.objects_in_view: Set[Any] = set()
        self.ground_map: Optional[bytes] = None
        self.size: Optional[Tuple[int, int]] = None
        self.tick_rate: Optional[int] = None

        self.ground_map_data: Dict[Tuple[int, int], chr] = {}
        self.solid_map_data: Dict[Tuple[int, int], chr] = {}
        self.roof_map_data: Dict[Tuple[int, int], chr] = {}

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
                elif isinstance(p, packet.ServerGroundMapFilePacket):
                    self.construct_map_data(p.payloads[0].value, mattype='ground')
                elif isinstance(p, packet.ServerSolidMapFilePacket):
                    self.construct_map_data(p.payloads[0].value, mattype='solid')
                elif isinstance(p, packet.ServerTickRatePacket):
                    self.tick_rate = p.payloads[0].value

            # Get volatile data such as player positions, etc.
            p: packet.Packet = packet.receive(self.s)

            if isinstance(p, packet.ServerPlayerPacket):
                player: models.Player = p.payloads[0].value
                pid: int = player.get_id()

                # If the received player is ourselves, update our player
                if pid == self.player.get_id():
                    self.player = player
                
                # If the received player is somebody else, either update the other player or add a new one in
                else:
                    # If the received player is already in view, update them
                    for o in self.objects_in_view:
                        if isinstance(o, models.Player) and o.get_id() == pid:
                            self.objects_in_view.remove(o)
                            self.objects_in_view.add(player)
                    # Otherwise, add them
                    self.objects_in_view.add(player)

            elif isinstance(p, packet.ServerLogPacket):
                self.logger.log(p.payloads[0].value)

            # Another player has logged out or disconnected so we remove them from the game.
            elif isinstance(p, packet.LogoutPacket) or isinstance(p, packet.DisconnectPacket):
                username: str = p.payloads[0].value
                for obj in self.objects_in_view:
                    if isinstance(obj, models.Player) and obj.get_username() == username and obj in self.objects_in_view:
                        self.objects_in_view.remove(obj)
                        break

            # Server sent back a goodbye packet indicating it's OK for us to exit the game.
            elif isinstance(p, packet.GoodbyePacket):
                self.stop()
                break

    def construct_map_data(self, map_file: List[str], mattype: str):
        """Load the coordinates of each type of ground material into a dictionary
           Should be accessed like self.ground_map_data[maps.STONE] which will return all coordinates where
           stone is found."""
        asciilist = maps.ml2asciilist(map_file)
        self.size = len(asciilist), len(asciilist[0])
        for y, row in enumerate(asciilist):
            for x, c in enumerate(row):
                if mattype == 'ground':
                    self.ground_map_data[(y, x)] = c
                elif mattype == 'solid':
                    self.solid_map_data[(y, x)] = c
                else:
                    raise NotImplementedError("I need to rethink the construction of different types of map data")

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
            packet.send(packet.LogoutPacket(self.player.get_username()), self.s)

        return key

    def chat(self, message: str) -> None:
        packet.send(packet.ChatPacket(message), self.s)

    def ready(self) -> bool:
        return False not in [bool(data) for data in (self.player, self.size, self.ground_map_data, self.tick_rate)]

    def stop(self) -> None:
        self._logged_in = False
        super().stop()

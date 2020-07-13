import curses
import curses.ascii
import socket
import threading
import time
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
        self.others: Set[models.Player] = set()
        self.walls: Optional[List[List[int, int]]] = None
        self.size: Optional[Tuple[int, int]] = None
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
                p: packet.Packet = packet.receive(self.s, debug=True)

                if isinstance(p, packet.ServerRoomSizePacket):
                    self.size = [p.payloads[0].value, p.payloads[1].value]
                elif isinstance(p, packet.ServerRoomPlayerPacket):
                    self.player = p.payloads[0].value
                elif isinstance(p, packet.ServerRoomGeometryPacket):
                    self.walls = p.payloads[0].value
                elif isinstance(p, packet.ServerRoomTickRatePacket):
                    self.tick_rate = p.payloads[0].value

            # Get volatile data such as player positions, etc.
            p: packet.Packet = packet.receive(self.s, debug=True)

            if isinstance(p, packet.ServerRoomPlayerPacket):
                player: models.Player = p.payloads[0].value
                pid: int = player.get_id()

                # If the received player is ourselves, update our player
                if pid == self.player.get_id():
                    self.player = player
                
                # If the received player is somebody else, either update the other player or add a new one in
                elif pid in [other.get_id() for other in self.others]:
                    for oid, o in [(other.get_id(), other) for other in self.others]:
                        if pid == oid:
                            self.others.remove(o)
                            self.others.add(player)

                else:
                    self.others.add(player)

            elif isinstance(p, packet.ServerLogPacket):
                self.logger.log(p.payloads[0].value)

            elif isinstance(p, packet.LogoutPacket):
                departed: models.Player = p.payloads[0].value
                for oid, o in [(other.get_id(), other) for other in self.others]:
                    if oid == departed.get_id():
                        self.others.remove(o)

            elif isinstance(p, packet.GoodbyePacket):
                self.stop()
                break

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
            packet.send(packet.LogoutPacket(), self.s)

        return key

    def chat(self, message: str) -> None:
        packet.send(packet.ChatPacket(message), self.s)

    def ready(self) -> bool:
        return None not in (self.player, self.size, self.walls, self.tick_rate)

    def stop(self) -> None:
        self._logged_in = False
        super().stop()

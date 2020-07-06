import curses
import json
import socket as sock
import sys
import time
import traceback
import threading
from typing import *

from networking import packet
from networking import models
from ..views.gameview import GameView
from .controller import Controller


class Game(Controller):
    def __init__(self, s: sock.socket):
        super().__init__()
        self.s: sock.socket = s

        # Game data
        self.player: Optional[models.Player] = None
        self.others: Set[models.Player] = set()
        self.walls: Optional[List[List[int, int]]] = None
        self.size: Optional[Tuple[int, int]] = None
        self.tick_rate: Optional[int] = None
        self.latest_log: Optional[str] = None

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
        f = open('packetdebug.txt', 'a')
        f.write(f"\nThread {threading.get_ident()}\ngame.receive_data() (game._logged_in = {self._logged_in})\n")
        while self._logged_in:
            f.write(f"\tGetting initial game data (game._logged_in = {self._logged_in})\n")
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

            f.write(f"\tGot initial game data (game._logged_in = {self._logged_in})\n")

            f.write(f"\tGetting volatile game data (game._logged_in = {self._logged_in})\n")


            # Get volatile data such as player positions, etc.
            p: packet.Packet = packet.receive(self.s, debug=True)


            f.write(f"\tGot volatile game data (game._logged_in = {self._logged_in})\n")
            f.write(f"\tHandling volatile game data (game._logged_in = {self._logged_in})\n")
            if isinstance(p, packet.ServerRoomPlayerPacket):
                player: Player = p.payloads[0].value
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

            elif isinstance(p, packet.ChatPacket):
                self.latest_log = p.payloads[0].value

            elif isinstance(p, packet.ServerLogPacket):
                self.latest_log = p.payloads[0].value

            elif isinstance(p, packet.DisconnectPacket):
                departed: Player = p.payloads[0].value
                for oid, o in [(other.get_id(), other) for other in self.others]:
                    if oid == departed.get_id():
                        self.others.remove(o)

            elif isinstance(p, packet.GoodbyePacket):
                self.stop()
                break

            f.write(f"\tHandled volatile game data\n")

        f.write(f"\tFinished receiving data (game._logged_in = {self._logged_in})\n")

    def get_input(self) -> None:
        super().get_input()
        key = self.view.stdscr.getch()

        # Movement
        if key == curses.KEY_UP:
            packet.send(packet.MoveUpPacket(), self.s)
        elif key == curses.KEY_RIGHT:
            packet.send(packet.MoveRightPacket(), self.s)
        elif key == curses.KEY_DOWN:
            packet.send(packet.MoveDownPacket(), self.s)
        elif key == curses.KEY_LEFT:
            packet.send(packet.MoveLeftPacket(), self.s)

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

        elif key == ord('q'):
            packet.send(packet.LogoutPacket(), self.s)

    def chat(self, message: str) -> None:
        try:
            packet.send(packet.ChatPacket(message), self.s)
        except sock.error:
            print("Error: Socket error. Traceback: ", file=sys.stderr)
            print(traceback.format_exc())

    def ready(self) -> bool:
        if self.player is None:
            return False
        return None not in (self.size, self.walls, self.tick_rate)

    def stop(self) -> None:
        self._logged_in = False
        self.view.stop()

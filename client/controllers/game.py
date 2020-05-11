import curses
import json
import socket as sock
import sys
import time
import traceback
from threading import Thread
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

    def start(self) -> None:
        # Listen for game data in its own thread
        Thread(target=self.receive_data, daemon=True).start()

        # Don't draw with game data until it's been received
        while not self.ready():
            time.sleep(0.2)

        # Start the view's display loop
        super().start()

    def receive_data(self) -> None:
        while True:
            # Get initial room data if not already done
            while not self.ready():
                p: packet.Packet = packet.receive(self.s)

                if isinstance(p, packet.ServerRoomSizePacket):
                    self.size = [p.payloads[0].value, p.payloads[1].value]
                elif isinstance(p, packet.ServerRoomPlayerPacket):
                    self.player = p.payloads[0].value
                elif isinstance(p, packet.ServerRoomGeometryPacket):
                    self.walls = p.payloads[0].value
                elif isinstance(p, packet.ServerRoomTickRatePacket):
                    self.tick_rate = p.payloads[0].value
            
            # Get volatile data such as player positions, etc.
            p: packet.Packet = packet.receive(self.s)
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

    def get_input(self) -> None:
        try:
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
            elif key in (curses.KEY_ENTER, curses.ascii.LF, curses.ascii.CR) and self.view.chatbox is not None:
                self.view.chatbox.modal()
                self.chat(self.view.chatbox.value)

        except KeyboardInterrupt:
           exit()

    # def move(self, direction: chr) -> None:
    #     packet.send(packet.MovePacket(self.player, direction), self.s)

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
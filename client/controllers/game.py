import curses
import json
import socket as sock
import sys
import time
import traceback
from threading import Thread
from typing import *

from networking import packet as pack
from ..views.gameview import GameView
from .controller import Controller


class Game(Controller):
    def __init__(self, s: sock.socket, addr: Tuple[str, int]):
        super().__init__()
        self.s: sock.socket = s
        self.addr: Tuple[str, int] = addr

        self.connected = False

        # Game data
        self.player_id: Optional[int] = None
        self.walls: Optional[List[List[int, int]]] = None
        self.size: Optional[Tuple[int, int]] = None
        self.tick_rate: Optional[int] = None

        # UI
        self.chatbox = None
        self.view = GameView(self)

    def connect(self) -> None:
        print("Trying to connect...")
        try:
            self.s.connect(self.addr)
        except OSError:
            # Most likely safe to ignore because socket should be already connected
            print(f"Error: Already connected. Traceback: ", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
        except Exception:
            print("Error: Unknown error. Traceback: ")
            print(traceback.format_exc())

        self.connected = True

    def disconnect(self) -> None:
        try:
            pack.sendpacket(pack.DisconnectPacket())
        except sock.error as e:
            print("Error: Socket error. Traceback: ", file=sys.stderr)
            print(traceback.format_exc())
            print(e, file=sys.stderr)
        self.s.close()

        self.connected = False

    def start(self) -> None:
        self.connect()

        # Listen for game data in its own thread
        Thread(target=self.load_game_data, daemon=True).start()

        # Don't draw with game data until it's been received
        while None in (self.size, self.player_id, self.walls, self.tick_rate):
            time.sleep(0.2)

        # Start the view's display thread
        super().start()

    def load_game_data(self) -> None:
        print("Getting data...")
        # Get initial room data if not already done
        while None in (self.size, self.player_id, self.walls, self.tick_rate):
            packet: Packet = pack.receivepacket(self.s)

            if isinstance(packet, pack.ServerRoomSizePacket):
                print(f"Got size: {packet.payloads}")
                self.size = packet.payloads
            elif isinstance(packet, pack.ServerRoomPlayerIdPacket):
                print(f"Got player_id: {packet.payloads[0]}")
                self.player_id = packet.payloads[0]
            elif isinstance(packet, pack.ServerRoomGeometryPacket):
                print(f"Got geometry: {packet.payloads[0]}")
                geometry: Dict[str, List[List[int, int]]] = packet.payloads[0]
                self.walls = geometry['walls']
            elif isinstance(packet, pack.ServerRoomTickRatePacket):
                print(f"Got tick_rate: {packet.payloads[0]}")
                self.tick_rate = packet.payloads[0]
        
        print("Got initial data")
        # Get volatile data such as player positions, etc.
        packet: Packet = pack.receivepacket(self.s)

    def get_input(self) -> None:
        try:
            key = self.view.stdscr.getch()

            # Movement
            if key == curses.KEY_UP:
                self.move('u')
            elif key == curses.KEY_RIGHT:
                self.move('r')
            elif key == curses.KEY_DOWN:
                self.move('d')
            elif key == curses.KEY_LEFT:
                self.move('l')

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

            elif key == ord('q'):
                self.disconnect()
                self.view.stop()

        except KeyboardInterrupt:
           self.disconnect()
           exit()

    def move(self, direction: chr) -> None:
        try:
            pack.sendpacket(pack.MovePacket(direction))
        except sock.error:
            print("Error: Socket error. Traceback: ", file=sys.stderr)
            print(traceback.format_exc())

    def chat(self, message: str) -> None:
        try:
            pack.sendpacket(pack.ChatPacket(message))
        except sock.error:
            print("Error: Socket error. Traceback: ", file=sys.stderr)
            print(traceback.format_exc())

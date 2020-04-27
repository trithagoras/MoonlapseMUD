import curses
import json
import socket as sock
import sys
import time
import traceback
from threading import Thread
from typing import *

from ..views.gameview import GameView
from .controller import Controller


class Game(Controller):
    def __init__(self, s: sock.socket, addr: Tuple[str, int]):
        super().__init__()
        self.s: sock.socket = s
        self.addr: Tuple[str, int] = addr

        self.connected = False

        self.player_id: int = 0
        self.game_data: dict = {}
        self.walls: list = []

        self.size: Tuple[int, int] = (-1, -1)
        self.tick_rate: int = -1

        # UI
        self.chatbox = None
        self.view = GameView(self)

    def connect(self) -> None:
        try:
            self.s.connect(self.addr)
        except sock.error:
            # Most likely safe to ignore because socket should be already connected
            print(f"Error: Connection refused. Traceback: ", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
        message: str = ""
        while True:
            try:
                message += self.s.recv(1).decode('utf-8')
            except sock.error as e:
                print("Error: Error receiving message. Traceback: ", file=sys.stderr)
                print(traceback.format_exc())
                self.chat("I got an error receiving a message!")

            if message[-1] == ";":
                if message[:-1] == 'full':
                    print('Session is full.')
                    sys.exit()
                else:
                    data = json.loads(message[:-1])
                    break

        self.size = (data['h'], data['w'])
        self.player_id = data['id']
        self.walls = data['walls']
        self.tick_rate = data['t']

        self.connected = True

    def disconnect(self) -> None:
        try:
            # Action: move, Payload: direction
            self.s.send(bytes(json.dumps({
                'a': 'bye'
            }) + ';', 'utf-8'))
        except sock.error as e:
            print("Error: Socket error. Traceback: ", file=sys.stderr)
            print(traceback.format_exc())
            print(e, file=sys.stderr)
        self.s.close()

        self.connected = False

    def start(self) -> None:
        self.connect()

        # Listen for game data in its own thread
        Thread(target=self.load_data, daemon=True).start()

        # Don't use game data until it's been received
        while self.game_data == {}:
            time.sleep(0.2)

        super().start()

    def load_data(self) -> None:
        message = ""
        while self.connected:
            try:
                message += self.s.recv(1).decode('utf-8')
                if message[-1] == ";":
                    if message[-2] != '\\':
                        # Terminate, end of JSON clause
                        self.game_data = json.loads(message[:-1])
                    else:
                        # Interpret as a literal
                        message = message[:-3] + ';'
                        continue
                    message = ""
            except sock.error:
                print("Error: Socket error. Traceback: ", file=sys.stderr)
                print(traceback.format_exc())
                message = ""

    def get_input(self) -> None:
        try:
            key = self.view.stdscr.getch()

            # Movement
            if key == curses.KEY_UP:
                self.move(0)
            elif key == curses.KEY_RIGHT:
                self.move(1)
            elif key == curses.KEY_DOWN:
                self.move(2)
            elif key == curses.KEY_LEFT:
                self.move(3)

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

    def move(self, direction: int) -> None:
        try:
            # Action: move, Payload: direction
            self.s.send(bytes(json.dumps({
                'a': 'm',
                'p': direction
            }) + ';', 'utf-8'))
        except sock.error:
            print("Error: Socket error. Traceback: ", file=sys.stderr)
            print(traceback.format_exc())

    def chat(self, message: str) -> None:
        # Sanitise semicolons
        message = message.replace(';', '\\;')

        try:
            # Action: chat, Payload: message
            self.s.send(bytes(json.dumps({
                'a': 'c',
                'p': message
            }) + ';', 'utf-8'))
        except sock.error:
            print("Error: Socket error. Traceback: ", file=sys.stderr)
            print(traceback.format_exc())

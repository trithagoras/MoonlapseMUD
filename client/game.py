import socket as sock
import json
import sys
import time
from threading import Thread
from typing import *
from curses_helper import Window, Curses
import curses.textpad as textpad
from view import View


class Game:
    def __init__(self, host: str, port: int):
        self.s: sock.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.address: Tuple[str, int] = (host, port)

        self.player_id: int = 0
        self.game_data: dict = {}
        self.walls: list = []

        self.size: Tuple[int, int] = (-1, -1)
        self.tick_rate: int = -1

        # UI
        self.focus: int = 1
        self.chatbox: Optional[textpad.Textbox] = None
        self.view: Optional[View] = None

    def connect(self) -> None:
        self.s.connect(self.address)
        message: str = ""
        while True:
            try:
                message += self.s.recv(1).decode('utf-8')
            except Exception as e:
                print(e, file=sys.stderr)
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

    def start(self, stdscr: Window, curses: Curses) -> None:
        # Listen for game data in its own thread
        Thread(target=self.load_data, daemon=True).start()

        # Initialise the view
        self.view = View(stdscr, curses, self)

        # Don't use game data until it's been received
        while self.game_data == {}:
            time.sleep(0.2)

        while True:
            self.view.draw(stdscr, curses)
            if stdscr.getmaxyx() < (self.view.height, self.view.width):
                time.sleep(0.2)
                continue

            self.get_player_input(stdscr, curses)

    def load_data(self) -> None:
        message = ""
        while True:
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
                message = ""

    def get_player_input(self, stdscr: Window, curses: Curses) -> None:
        try:
            key = stdscr.getch()

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
            elif key in [ord('1'), ord('2'), ord('3')]:
                self.focus = int(chr(key))

            # Chat
            elif key in (curses.KEY_ENTER, ord('\n'), ord('\r')) and self.view.win3 is not None:
                self.focus = 4
                self.chatbox = textpad.Textbox(self.view.chatwin)
                curses.curs_set(True)

            elif key == ord('q'):
                exit()

        except KeyboardInterrupt:
            exit()

        if self.chatbox is not None:
            self.handle_chatbox(curses)

    def move(self, direction: int) -> None:
        try:
            # Action: move, Payload: direction
            self.s.send(bytes(json.dumps({
                'a': 'm',
                'p': direction
            }) + ';', 'utf-8'))
        except sock.error:
            pass

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
            pass

    @staticmethod
    def validate_chatbox(k):
        # https://docs.python.org/3/library/curses.html#module-curses
        if k in (ord('\n'), ord('\r')):
            return 7
        if str(chr(k)) == '\b' or k == 127:
            return 8
        return k

    def handle_chatbox(self, curses: Curses) -> None:
        # https://stackoverflow.com/questions/36121802/python-curses-make-enter-key-terminate-textbox
        message: str = self.chatbox.edit(self.validate_chatbox)
        if len(message) > 0:
            self.chat(message)
        self.chatbox = None
        self.view.chatwin.clear()
        curses.curs_set(False)

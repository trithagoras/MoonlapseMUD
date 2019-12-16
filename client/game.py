import socket as sock
import json, sys, time
from threading import Thread
from payload import move
from typing import *
from curses_helper import Window, Curses
import curses.textpad as textpad
from view import View


class Game:
    def __init__(self, host: str, port: int):
        self.s: sock.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.address: Tuple[str, int] = (host, port)

        self.player_id: int = 0
        self.game_data = {}
        self.walls = []

        self.size: Tuple[int, int] = (-1, -1)
        self.tick_rate: int = -1

        # UI
        self.focus: int = 1
        self.chatbox: Optional[textpad.Textbox] = None
        self.view: Optional[View] = None

    def move(self, direction: move.Direction):
        try:
            # Action: move, Payload: direction
            self.s.send(bytes(json.dumps({
                'a': 'm',
                'p': direction
            }) + ';', 'utf-8'))
        except sock.error:
            pass

    def chat(self, message: str):
        delimiter: str = "Say: "
        try:
            # Action: chat, Payload: message
            self.s.send(bytes(json.dumps({
                'a': 'c',
                'p': message[message.index(delimiter) + len(delimiter):]  # Strip, e.g. "Say: "
            }) + ';', 'utf-8'))
        except sock.error:
            pass

    def connect(self):
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

    def start(self, stdscr: Window, curses: Curses):
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

    def handle_chatbox(self):
        # https://stackoverflow.com/questions/36121802/python-curses-make-enter-key-terminate-textbox
        message: str = self.chatbox.edit(lambda k: 7 if k in (ord('\n'), '\r') else k)
        self.chat(message)
        self.chatbox = None

    def get_player_input(self, stdscr: Window, curses: Curses):
        try:
            key = stdscr.getch()

            # Movement
            if key == curses.KEY_UP:
                self.move(move.Direction.UP)
            elif key == curses.KEY_RIGHT:
                self.move(move.Direction.RIGHT)
            elif key == curses.KEY_DOWN:
                self.move(move.Direction.DOWN)
            elif key == curses.KEY_LEFT:
                self.move(move.Direction.LEFT)

            # Changing window focus
            elif key in [ord('1'), ord('2'), ord('3')]:
                self.focus = int(chr(key))

            # Chat
            elif key in (curses.KEY_ENTER, ord('\n'), ord('\r')) and self.view.win3 is not None:
                self.focus = 4
                self.chatbox = textpad.Textbox(self.view.chatwin)

        except KeyboardInterrupt:
            exit()

        if self.chatbox is not None:
            self.handle_chatbox()

    def load_data(self):
        message = ""
        while True:
            try:
                message += self.s.recv(1).decode('utf-8')
                if message[-1] == ";":
                    self.game_data = json.loads(message[:-1])
                    message = ""
            except sock.error:
                message = ""

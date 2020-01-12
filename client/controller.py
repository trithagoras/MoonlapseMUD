import socket as sock
import json
import sys
import time
from threading import Thread
from typing import *
import curses.textpad as textpad
from view import GameView, Window2Focus, MenuView, View
import curses as ncurses


class Controller:
    def __init__(self):
        self.view: View = View(self)

    def start(self):
        ncurses.wrapper(self.view.display)

    def get_input(self) -> None:
        pass


class Menu(Controller):
    def __init__(self, menu):
        super().__init__()
        self.menu = menu
        self.cursor: int = 0
        self.view = MenuView(self)

    def get_input(self) -> None:
        try:
            key = self.view.stdscr.getch()

            # Movement
            if key == ncurses.KEY_UP:
                self.cursor = max(self.cursor - 1, 0)
            elif key == ncurses.KEY_DOWN:
                self.cursor = min(self.cursor + 1, len(self.menu) - 1)
            elif key in (ncurses.KEY_ENTER, ord('\n'), ord('\r')):
                fn = self.menu[list(self.menu.keys())[self.cursor]]
                if fn is not None:
                    fn()
            elif key == ord('q'):
                exit()

        except KeyboardInterrupt:
            exit()


class MainMenu(Menu):
    def __init__(self, hostname, port):
        super().__init__({
            "Play": self.play,
            "Login": self.login,
            "Register": self.register
        })

        self.hostname =  hostname
        self.port = port

        self.view = MenuView(self, f"Welcome to {hostname}:{port}")

    def play(self):
        game = Game(self.hostname, self.port)
        game.start()

    def login(self):
        loginmenu = LoginMenu()
        loginmenu.start()

    def register(self):
        registermenu = RegisterMenu()
        registermenu.start()


class LoginMenu(Menu):
    def __init__(self):
        super().__init__({
            "Username": None,
            "Password": None,
            "Remember me": None
        })

        self.view = MenuView(self, "Login")


class RegisterMenu(Menu):
    def __init__(self):
        super().__init__({
            "Email": None,
            "Username": None,
            "Password": None,
            "Sign up for newsletter": None
        })

        self.view = MenuView(self, "Registration")


class Game(Controller):
    def __init__(self, host: str, port: int):
        super().__init__()
        self.s: sock.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.address: Tuple[str, int] = (host, port)

        self.player_id: int = 0
        self.game_data: dict = {}
        self.walls: list = []

        self.size: Tuple[int, int] = (-1, -1)
        self.tick_rate: int = -1

        # UI
        self.chatbox: Optional[textpad.Textbox] = None
        self.view = GameView(self)

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

    def get_input(self) -> None:
        try:
            key = self.view.stdscr.getch()

            # Movement
            if key == ncurses.KEY_UP:
                self.move(0)
            elif key == ncurses.KEY_RIGHT:
                self.move(1)
            elif key == ncurses.KEY_DOWN:
                self.move(2)
            elif key == ncurses.KEY_LEFT:
                self.move(3)

            # Changing window focus
            elif key in [ord('1'), ord('2'), ord('3')]:
                self.view.focus = int(chr(key))

            # Changing window 2 focus
            elif key == ord('?'):
                self.view.win2_focus = Window2Focus.HELP
            elif key == ord('k'):
                self.view.win2_focus = Window2Focus.SKILLS
            elif key == ord('i'):
                self.view.win2_focus = Window2Focus.INVENTORY
            elif key == ord('p'):
                self.view.win2_focus = Window2Focus.SPELLBOOK
            elif key == ord('g'):
                self.view.win2_focus = Window2Focus.GUILD
            elif key == ord('j'):
                self.view.win2_focus = Window2Focus.JOURNAL

            # Chat
            elif key in (ncurses.KEY_ENTER, ord('\n'), ord('\r')) and self.view.win3 is not None:
                self.chatbox = textpad.Textbox(self.view.chatwin)
                ncurses.curs_set(True)

            elif key == ord('q'):
                exit()

        except KeyboardInterrupt:
            exit()

        if self.chatbox is not None:
            self.handle_chatbox()

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
        if k == 127:
            return 8
        return k

    def handle_chatbox(self) -> None:
        # https://stackoverflow.com/questions/36121802/python-curses-make-enter-key-terminate-textbox
        message: str = self.chatbox.edit(self.validate_chatbox)
        if len(message) > 0:
            self.chat(message)
        self.chatbox = None
        self.view.chatwin.clear()
        ncurses.curs_set(False)
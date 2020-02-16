import socket as sock
import json
import sys
import time
from threading import Thread
from typing import *
import curses.textpad as textpad
from view import *
import curses as ncurses


class Controller:
    def __init__(self):
        self.view: View = View(self)

    def start(self):
        ncurses.wrapper(self.view.display)

    def get_input(self) -> None:
        pass

    @staticmethod
    def validate_textbox(k):
        # https://docs.python.org/3/library/curses.html#module-curses
        if k in (ord('\n'), ord('\r')):
            return 7
        if k == 127:
            return 8
        return k


class Menu(Controller):
    def __init__(self, menu):
        super().__init__()
        self.menu = menu
        self.cursor: int = 0
        self.view = MenuView(self)

    def get_input(self) -> int:
        key = self.view.stdscr.getch()

        # Movement
        if key == ncurses.KEY_UP:
            self.cursor = max(self.cursor - 1, 0)
        elif key == ncurses.KEY_DOWN:
            self.cursor = min(self.cursor + 1, len(self.menu) - 1)
        elif key == ord('\t'):
            self.cursor = (self.cursor + 1) % len(self.menu)
        elif key in (ncurses.KEY_ENTER, ord('\n'), ord('\r')):
            fn = self.menu[list(self.menu.keys())[self.cursor]]
            if fn is not None:
                fn()
        elif key == ord('q'):
            self.view.stop()

        return key


class MainMenu(Menu):
    def __init__(self, host, port):
        super().__init__({
            "Login": self.login,
            "Register": self.register
        })

        self.host = host
        self.port = port

        self.view = MenuView(self, f"Welcome to {host}:{port}")

    def login(self):
        loginmenu = LoginMenu(self.host, self.port)
        loginmenu.start()
        self.start()

    def register(self):
        registermenu = RegisterMenu(self.host, self.port)
        registermenu.start()
        self.start()


class LoginMenu(Menu):
    def __init__(self, host, port):
        self.username: str = ''
        self.password: str = ''

        self.s: sock.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.address = (host, port)

        super().__init__({
            "Username": self.login,
            "Password": self.login,
            "Remember me": None
        })

        self.view = LoginView(self)

    def start(self):
        try:
            self.s.connect(self.address)
        except sock.error:
            # Socket probably closed, retry connection
            self.s: sock.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self.s.connect(self.address)
        super().start()

    def get_input(self) -> int:
        key = super().get_input()
        if key in range(32, 127):
            self.handle_box(chr(key))
        return key

    def login(self):
        if '' in (self.username, self.password):
            self.view.title = "Username or password must not be blank"
            return

        self.view.title = f"Attempted login in as {self.username} with password {self.password}"
        try:
            self.s.send(bytes(json.dumps({
                'a': 'login',
                'p': self.username,
                'p2': self.password
            }) + ';', 'utf-8'))

            game = Game(self.s, self.address)
            game.start()
            self.start()

        except sock.error as e:
            self.view.title = str(e)

    def handle_box(self, first_key: chr) -> None:
        ncurses.curs_set(True)
        if self.cursor == 0:
            self.view.win1.clear()
            self.view.win1.addch(0, 0, first_key)
            self.username = self.view.usernamebox.edit(self.validate_textbox).strip()
        elif self.cursor == 1:
            self.view.win2.clear()
            self.view.win2.addch(0, 0, first_key)
            self.password = self.view.passwordbox.edit(self.validate_textbox).strip()
        ncurses.curs_set(False)


class RegisterMenu(Menu):
    def __init__(self, host, port):
        self.username: str = ''
        self.password: str = ''
        self.confirmpassword: str = ''

        self.s: sock.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.address = (host, port)

        super().__init__({
            "Username": self.register,
            "Password": self.register,
            "Confirm password": self.register
        })

        self.view = RegisterView(self)

    def start(self):
        self.s.connect(self.address)
        super().start()

    def get_input(self) -> int:
        key = super().get_input()
        if key in range(32, 127):
            self.handle_box(chr(key))
        return key

    def register(self):
        if '' in (self.username, self.password, self.confirmpassword):
            self.view.title = "Field must not be blank"
            return

        self.view.title = f"Attempted registration as {self.username} with password {self.password}"

        if self.password != self.confirmpassword:
            self.view.title = "Passwords do not match!"
            return

        try:
            self.s.send(bytes(json.dumps({
                'a': 'register',
                'p': self.username,
                'p2': self.password
            }) + ';', 'utf-8'))

        except sock.error as e:
            self.view.title = str(e)

    def handle_box(self, first_key: chr) -> None:
        ncurses.curs_set(True)
        if self.cursor == 0:
            self.view.win1.clear()
            self.view.win1.addch(0, 0, first_key)
            self.username = self.view.usernamebox.edit(self.validate_textbox).strip()
        elif self.cursor == 1:
            self.view.win2.clear()
            self.view.win2.addch(0, 0, first_key)
            self.password = self.view.passwordbox.edit(self.validate_textbox).strip()
        elif self.cursor == 2:
            self.view.win3.clear()
            self.view.win3.addch(0, 0, first_key)
            self.confirmpassword = self.view.confirmpasswordbox.edit(self.validate_textbox).strip()
        ncurses.curs_set(False)


class Game(Controller):
    def __init__(self, s: sock.socket, address: Tuple[str, int]):
        super().__init__()
        self.s: sock.socket = s
        self.address: Tuple[str, int] = address

        self.connected = False

        self.player_id: int = 0
        self.game_data: dict = {}
        self.walls: list = []

        self.size: Tuple[int, int] = (-1, -1)
        self.tick_rate: int = -1

        # UI
        self.chatbox: Optional[textpad.Textbox] = None
        self.view = GameView(self)

    def connect(self) -> None:
        try:
            self.s.connect(self.address)
        except sock.error as e:
            # Most likely safe to ignore because socket should be already connected
            print(e, sys.stderr)
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

        self.connected = True

    def disconnect(self) -> None:
        try:
            # Action: move, Payload: direction
            self.s.send(bytes(json.dumps({
                'a': 'bye'
            }) + ';', 'utf-8'))
        except sock.error as e:
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
                self.disconnect()
                self.view.stop()

        except KeyboardInterrupt:
           self.disconnect()
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

    def handle_chatbox(self) -> None:
        # https://stackoverflow.com/questions/36121802/python-curses-make-enter-key-terminate-textbox
        message: str = self.chatbox.edit(self.validate_textbox)
        if len(message) > 0:
            self.chat(message)
        self.chatbox = None
        self.view.chatwin.clear()
        ncurses.curs_set(False)

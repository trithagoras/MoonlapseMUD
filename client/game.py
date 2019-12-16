import socket as sock
import json
import sys
import curses as ncurses
from time import sleep
from threading import Thread
from payload import move
from typing import *
from curses_helper import Window, Curses
import curses.textpad as textpad


class Game:
    def __init__(self, host: str, port: int):
        self.s: sock.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.address: Tuple[str, int] = (host, port)

        self.player_id: int = 0
        self.game = {}
        self.walls = []

        self.size: Tuple[int, int] = (-1, -1)
        self.tick_rate: int = -1

        # UI
        self.focus: int = 1
        self.textbox: Optional[textpad.Textbox] = None
        self.win1: Optional[Window] = None
        self.win2: Optional[Window] = None
        self.win3: Optional[Window] = None

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
        try:
            # Action: chat, Payload: message
            self.s.send(bytes(json.dumps({
                'a': 'c',
                'p': message
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

    def start(self):
        self.listen()
        ncurses.wrapper(self.draw, ncurses)

    def listen(self):
        Thread(target=self.update, daemon=True).start()

    def handle_chatbox(self):
        # https://stackoverflow.com/questions/36121802/python-curses-make-enter-key-terminate-textbox
        message: str = self.textbox.edit(lambda k: 7 if k in (ord('\n'), '\r') else k)
        self.chat(message)
        self.textbox = None

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
            elif key in (curses.KEY_ENTER, ord('\n'), ord('\r')) and self.win3 is not None:
                self.focus = 4
                self.textbox = textpad.Textbox(self.win3)

        except KeyboardInterrupt:
            exit()

        if self.textbox is not None:
            self.handle_chatbox()

    def update(self):
        message = ""
        while True:
            try:
                message += self.s.recv(1).decode('utf-8')
                if message[-1] == ";":
                    self.game = json.loads(message[:-1])
                    message = ""
            except sock.error:
                message = ""

    def draw(self, stdscr: Window, curses: Curses):
        stdscr.keypad(1)
        stdscr.timeout(round(1000 / self.tick_rate))
        curses.curs_set(False)

        # init window sizes
        height, width = (46, 106)

        win1_height, win1_width = (23, 53)
        win1_y, win1_x = (9, 0)
        win2_height, win2_width = (23, 53)
        win2_y, win2_x = (9, 53)
        win3_height, win3_width = (14, 106)
        win3_y, win3_x = (32, 0)

        # Init windows
        self.win1 = stdscr.subwin(win1_height, win1_width, win1_y, win1_x)
        self.win2 = stdscr.subwin(win2_height, win2_width, win2_y, win2_x)
        self.win3 = stdscr.subwin(win3_height, win3_width, win3_y, win3_x)

        # Start colors in curses
        curses.start_color()

        # init color pairs
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

        while self.game == {}:
            sleep(0.2)

        while True:
            stdscr.erase()

            # max terminal size
            if stdscr.getmaxyx() < (46, 106):
                stdscr.addstr(0, 0, f"Must be {height} rows x {width} cols")
                stdscr.refresh()
            else:
                # Window controls labels
                stdscr.hline(0, 0, curses.ACS_HLINE, width)
                stdscr.addstr(0, 2, "Window Controls ")
                stdscr.addstr(1, 1, "[1/2/3] Change window focus  [ENTER] Chat")
                stdscr.addstr(3, 2, "[M] Map  [T] Travel")

                stdscr.addstr(3, win2_x + 2, "[I] Inventory  [P] Spellbook  [B] Equipment")
                stdscr.addstr(4, win2_x + 2, "[G] Guild      [K] Skills")

                # Map controls labels
                stdscr.hline(6, 0, curses.ACS_HLINE, width)
                stdscr.addstr(6, 2, "Map Controls ")
                stdscr.addstr(7, 1,
                              "[V] Look  [D] Pick up item  [E] Use/Equip  [←/→/↑/↓] Move  [</>] Use Stairs/Ladders")

                # Adding border to windows
                self.win1.border()
                self.win2.border()
                self.win3.border()

                # Rendering window titles
                if self.focus == 1:
                    self.win1.addstr(0, 2, "[1] Forgotten Moor ", curses.color_pair(3))
                else:
                    self.win1.addstr(0, 2, "[1] Forgotten Moor ")

                if self.focus == 2:
                    self.win2.addstr(0, 2, "[2] Skills ", curses.color_pair(3))
                else:
                    self.win2.addstr(0, 2, "[2] Skills ")

                if self.focus == 3:
                    self.win3.addstr(0, 2, "[3] Log ", curses.color_pair(3))
                else:
                    self.win3.addstr(0, 2, "[3] Log ")

                # win1 content
                for index in range(0, len(self.game['p'])):
                    player = self.game['p'][index]

                    if player is not None:
                        self.win1.addch(player['pos']['y'] + 1, player['pos']['x'], player['c'])

                for wall in self.walls:
                    self.win1.addch(wall[1] + 1, wall[0], '█')

                # Window 2 content
                self.win2.addstr(1, 1, "coreyb65, Guardian of Forgotten Moor")
                self.win2.addstr(3, 1, f"Level 15 {progress_bar(7, 10)} (7/10 skill levels to 16)")

                self.win2.addstr(5, 1, f"Vitality      31/31 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(6, 1, f"Strength      10/10 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(7, 1, f"Agility       31/31 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(8, 1, f"Dexterity     31/31 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(9, 1, f"Astrology     31/31 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(10, 1, f"Intelligence  31/31 {progress_bar(3, 10)} (3,000/10,000)")

                self.win2.addstr(12, 1, f"Woodcutting   31/31 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(13, 1, f"Crafting      31/31 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(14, 1, f"Mining        31/31 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(15, 1, f"Smithing      31/31 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(16, 1, f"Fishing       31/31 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(17, 1, f"Cooking       31/31 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(18, 1, f"Alchemy       31/31 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(19, 1, f"Enchanting    31/31 {progress_bar(3, 10)} (3,000/10,000)")
                self.win2.addstr(20, 1, f"??????????    31/31 {progress_bar(3, 10)} (3,000/10,000)")

                # Window 3 content
                self.win3.hline(win3_height - 3, 1, curses.ACS_HLINE, win3_width - 2)
                self.win3.addstr(win3_height - 2, 2, "Say: ")

                # sample lines in win3
                self.win3.addstr(3, 1, "[14:22] coreyb65 says: Hello and welcome to Moonlapse!")
                self.win3.addstr(4, 1, "[14:25] A forbidden void has opened in the Forgotten Moor!",
                            curses.color_pair(6))

                # get input (last line)
                self.get_player_input(stdscr, curses)


def progress_bar(value: float, max_value: float) -> str:
    percent = int(10 * (value / max_value)) + 1

    s = "[-----------]"
    s = s[:percent] + "o" + s[percent + 1:]
    return s

import socket as sock
import json, sys, curses
from time import sleep
from threading import Thread
from payload import move
from typing import *
from curses_helper import Window


class Game:
    def __init__(self, host: str, port: int):
        self.s: sock.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.address: Tuple[str, int] = (host, port)

        self.player_id: int = 0
        self.game = {}
        self.walls = []

        self.size: Tuple[int, int] = (-1, -1)
        self.tick_rate: int = -1
        self.window: Optional[Window] = None

    def move(self, direction: move.Direction):
        try:
            # Action: Move, payload: direction
            self.s.send(bytes(json.dumps({
                'a': 'm',
                'p': direction
            }) + ";", "utf-8"))
        except sock.error:
            pass

    def connect(self):
        self.s.connect(self.address)
        message: str = ""
        while True:
            message += self.s.recv(1).decode('utf-8')
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

        self.window = curses.newwin(self.size[0], self.size[1], 0, 0)
        self.window.keypad(1)
        self.window.timeout(round(1000 / self.tick_rate))

    def start(self):
        self.listen()
        self.getPlayerInput()

    def listen(self):
        Thread(target=self.update, daemon=True).start()

    def getPlayerInput(self):
        while self.game == {}:
            sleep(0.2)

        while True:
            try:
                key = self.window.getch()

                if key == curses.KEY_UP:
                    self.move(move.Direction.UP)
                elif key == curses.KEY_RIGHT:
                    self.move(move.Direction.RIGHT)
                elif key == curses.KEY_DOWN:
                    self.move(move.Direction.DOWN)
                elif key == curses.KEY_LEFT:
                    self.move(move.Direction.LEFT)

                self.draw()

            except KeyboardInterrupt:
                break

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

    def draw(self):
        self.window.erase()
        self.window.border(0)

        for index in range(0, len(self.game['p'])):
            player = self.game['p'][index]

            if player is not None:
                self.window.addch(player['pos']['y'], player['pos']['x'], player['c'])

        self.window.addstr(0, 2, "Moonlapse MUD 0.1")

        for wall in self.walls:
            self.window.addch(wall[1], wall[0], '▓')
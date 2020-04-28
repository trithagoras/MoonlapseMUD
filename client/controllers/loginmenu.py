import curses
import json
import socket as sock
import sys
import traceback

from networking import packet as pack
from ..views.loginview import LoginView
from .game import Game
from .networkmenu import NetworkMenu


class LoginMenu(NetworkMenu):
    def __init__(self, host, port):
        self.username: str = ''
        self.password: str = ''

        super().__init__(host, port, {
            "Username": self.login,
            "Password": self.login
        })

        self.view = LoginView(self)

    def get_input(self) -> int:
        key = super().get_input()
        if curses.ascii.isprint(key) or key in (curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_DC):
            if self.cursor == 0:
                self.view.usernamebox.modal(first_key=key)
                self.username = self.view.usernamebox.value
            elif self.cursor == 1:
                self.view.passwordbox.modal(first_key=key)
                self.password = self.view.passwordbox.value
        return key

    def login(self):
        if '' in (self.username, self.password):
            self.view.title = "Username or password must not be blank"
            return

        self.view.title = f"Attempted login in as {self.username} with password {self.password}"
        try:
            pack.sendpacket(self.s, pack.LoginPacket(self.username, self.password))

            game = Game(self.s, self.addr)
            game.start()
            self.start()

        except sock.error as e:
            print("Error: Socket error. Traceback: ", file=sys.stderr)
            print(traceback.format_exc())
            self.view.title = str(e)

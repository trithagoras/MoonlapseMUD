import curses
import json
import socket
import sys
import traceback

from networking import packet
from ..views.loginview import LoginView
from .game import Game
from .menu import Menu


class LoginMenu(Menu):
    def __init__(self, s: socket.socket):
        self.s: socket.socket = s
        self.username: str = ''
        self.password: str = ''

        super().__init__({
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
        packet.send(packet.LoginPacket(self.username, self.password), self.s)
        
        response: Union[packet.OkPacket, packet.DenyPacket] = packet.receive(self.s)
        if isinstance(response, packet.OkPacket):
            game = Game(self.s)
            game.start()
            self.start()
        
        else:
            self.view.title = response.payloads[0].value

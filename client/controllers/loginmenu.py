import curses
import curses.ascii
import socket
from networking import packet
from typing import *
from .game import Game
from .menu import Menu
from ..views.loginview import LoginView


class LoginMenu(Menu):
    def __init__(self, s: socket.socket):
        self.s: socket.socket = s
        self.username: str = ''
        self.password: str = ''

        super().__init__({
            "Username": self.login,
            "Password": self.login
        })

        self.view = LoginView(self, title="Please enter your username and password")

    def handle_input(self) -> int:
        key = super().handle_input()
        if curses.ascii.isprint(key) or key in (curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_DC):
            if self.cursor == 0:
                self.view.usernamebox.modal(first_key=key)
                self.username = self.view.usernamebox.value
            elif self.cursor == 1:
                self.view.passwordbox.modal(first_key=key)
                self.password = self.view.passwordbox.value
        return key

    def login(self) -> None:
        if '' in (self.username, self.password):
            self.view.title = "Username or password must not be blank"
            return

        self.view.title = "Please wait..."
        packet.send(packet.LoginPacket(self.username, self.password), self.s)
        self.view.title = "Sent login request..."
        try:
            response: Union[packet.OkPacket, packet.DenyPacket] = packet.receive(self.s)
        except Exception as e:
            self.view.title = str(e)
        else:
            self.view.title = "Got response..."
            if isinstance(response, packet.OkPacket):
                self.view.title = "Entering game..."
                Game(self.s).start()
                self.start()       
            elif isinstance(response, packet.DenyPacket):
                self.view.title = response.payloads[0].value
            else:
                self.view.title = "Unexpected error. Please try again."

import curses
import json
import socket
import sys
import traceback

from networking import packet
from ..views.registerview import RegisterView
from .menu import Menu


class RegisterMenu(Menu):
    def __init__(self, s: socket.socket):
        self.s: socket.socket = s
        self.username: str = ''
        self.password: str = ''
        self.confirmpassword: str = ''

        super().__init__({
            "Username": self.register,
            "Password": self.register,
            "Confirm password": self.register
        })

        self.view = RegisterView(self)

    def start(self) -> None:
        self.view.title = "Please enter your desired username and password"
        super().start()

    def get_input(self) -> int:
        key = super().get_input()
        if curses.ascii.isprint(key) or key in (curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_DC):
            if self.cursor == 0:
                self.view.usernamebox.modal(first_key=key)
                self.username = self.view.usernamebox.value
            elif self.cursor == 1:
                self.view.passwordbox.modal(first_key=key)
                self.password = self.view.passwordbox.value
            elif self.cursor == 2:
                self.view.confirmpasswordbox.modal(first_key=key)
                self.confirmpassword = self.view.confirmpasswordbox.value
        return key

    def register(self):
        if '' in (self.username, self.password, self.confirmpassword):
            self.view.title = "Field must not be blank"
            return

        self.view.title = f"Attempted registration as {self.username} with password {self.password}"

        if self.password != self.confirmpassword:
            self.view.title = "Passwords do not match!"
            return

        packet.send(packet.RegisterPacket(self.username, self.password), self.s)

        response: Union[packet.OkPacket, packet.DenyPacket] = packet.receive(self.s)

        if isinstance(response, packet.OkPacket):
            self.view.title = "Registration successful! Press CTRL+C or ESC to go back and log in."
        else:
            self.view.title = response.payloads[0].value
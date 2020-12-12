import curses
import curses.ascii
import socket
from networking import packet
from typing import *
from .menu import Menu
from ..views.registerview import RegisterView


class RegisterMenu(Menu):
    def __init__(self, s: socket.socket):
        self.s: socket.socket = s
        self.username: str = ''
        self.password: str = ''
        self.confirmpassword: str = ''
        self.char: chr = ''

        super().__init__({
            "Username": self.register,
            "Password": self.register,
            "Confirm password": self.register,
            "Character": self.register
        })

        self.view = RegisterView(self, title="Please enter your desired username and password\n" +
                                             "Also enter a character you want to look like")

    def handle_input(self) -> int:
        key = super().handle_input()
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
            elif self.cursor == 3:
                self.view.charbox.modal(first_key=key)
                self.char = self.view.charbox.value
        return key

    def register(self):
        if '' in (self.username, self.password, self.confirmpassword, self.char):
            self.view.title = "Field must not be blank"
            return

        self.view.title = f"Attempted registration as {self.username} with password {self.password} and character {self.char}"

        if self.password != self.confirmpassword:
            self.view.title = "Passwords do not match!"
            return

        if len(self.char) != 1:
            self.view.title = "Character length must be 1"
            return

        packet.send(packet.RegisterPacket(self.username, self.password, self.char), self.s)

        response: Union[packet.OkPacket, packet.DenyPacket] = packet.receive(self.s)

        if isinstance(response, packet.OkPacket):
            self.view.title = "Registration successful! Press CTRL+C or ESC to go back and log in."
        elif isinstance(response, packet.DenyPacket):
            self.view.title = response.payloads[0].value
        else:
            self.view.title = "Unexpected error. Please try again."

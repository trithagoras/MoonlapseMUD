import curses
import socket as sock
import traceback
import json
import sys
from .networkmenu import NetworkMenu
from ..views.registerview import RegisterView


class RegisterMenu(NetworkMenu):
    def __init__(self, host, port):
        self.username: str = ''
        self.password: str = ''
        self.confirmpassword: str = ''

        super().__init__(host, port, {
            "Username": self.register,
            "Password": self.register,
            "Confirm password": self.register
        })

        self.view = RegisterView(self)

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

        try:
            self.s.send(bytes(json.dumps({
                'a': 'register',
                'p': self.username,
                'p2': self.password
            }) + ';', 'utf-8'))

        except sock.error as e:
            print("Error: Socket error. Traceback: ", file=sys.stderr)
            print(traceback.format_exc())
            self.view.title = str(e)

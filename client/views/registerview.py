from typing import *
from .menuview import MenuView
from ..curses_helper import TextBox


class RegisterView(MenuView):
    def __init__(self, controller):
        super().__init__(controller)

        self.username: str = ''
        self.password: str = ''
        self.confirmpassword: str = ''

        self.usernamebox: Optional[TextBox] = None
        self.passwordbox: Optional[TextBox] = None
        self.confirmpasswordbox: Optional[TextBox] = None

    def display(self, stdscr):
        self.stdscr = stdscr
        self.usernamebox = TextBox(stdscr, 6, 30, 20)
        self.passwordbox = TextBox(stdscr, 9, 30, 20)
        self.confirmpasswordbox = TextBox(stdscr, 12, 30, 20)

        super().display(stdscr)

    def draw(self):
        super().draw()

        self.stdscr.addstr(6, 30, self.controller.username)
        self.stdscr.addstr(9, 30, self.controller.password)
        self.stdscr.addstr(12, 30, self.controller.confirmpassword)

        self.stdscr.move(6 + self.controller.cursor * 3, 30)

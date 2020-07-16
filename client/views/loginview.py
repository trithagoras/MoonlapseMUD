from typing import *
from .menuview import MenuView
from ..curses_helper import TextBox


class LoginView(MenuView):
    def __init__(self, controller, title: Optional[str] = None):
        super().__init__(controller, title=title)

        self.username: str = ''
        self.password: str = ''

        self.usernamebox: Optional[TextBox] = None
        self.passwordbox: Optional[TextBox] = None

    def display(self, stdscr):
        self.stdscr = stdscr
        self.usernamebox = TextBox(stdscr, 6, 20, 20)
        self.passwordbox = TextBox(stdscr, 9, 20, 20)

        super().display(stdscr)

    def draw(self):
        super().draw()

        self.stdscr.addstr(6, 20, self.controller.username)
        self.stdscr.addstr(9, 20, self.controller.password)

        self.stdscr.move(6 + self.controller.cursor * 3, 20)

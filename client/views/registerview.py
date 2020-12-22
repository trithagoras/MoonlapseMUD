from typing import *
from .menuview import MenuView
from ..curses_helper import TextBox


class RegisterView(MenuView):
    def __init__(self, controller, title: Optional[str] = None):
        super().__init__(controller, title=title)

        self.username: str = ''
        self.password: str = ''
        self.confirmpassword: str = ''
        self.char: chr = ''

        self.usernamebox: Optional[TextBox] = None
        self.passwordbox: Optional[TextBox] = None
        self.confirmpasswordbox: Optional[TextBox] = None
        self.charbox: Optional[TextBox] = None

    def display(self, stdscr):
        self.stdscr = stdscr
        self.usernamebox = TextBox(stdscr, 6, 30, 20)
        self.passwordbox = TextBox(stdscr, 9, 30, 20, censored=True)
        self.confirmpasswordbox = TextBox(stdscr, 12, 30, 20, censored=True)
        self.charbox = TextBox(stdscr, 15, 30, 20)

        super().display(stdscr)

    def draw(self):
        super().draw()

        self.stdscr.addstr(6, 30, self.usernamebox.display_value())
        self.stdscr.addstr(9, 30, self.passwordbox.display_value())
        self.stdscr.addstr(12, 30, self.confirmpasswordbox.display_value())
        self.stdscr.addstr(15, 30, self.charbox.display_value())

        self.stdscr.move(6 + self.controller.cursor * 3, 30)

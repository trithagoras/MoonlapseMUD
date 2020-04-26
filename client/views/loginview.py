import curses_helper
import curses
import time
from .menuview import MenuView


class LoginView(MenuView):
    def __init__(self, controller):
        self.username: str = ''
        self.password: str = ''

        # Textboxes are initialised once the controller passes stdscr to the display method.
        self.usernamebox = None
        self.passwordbox = None

        super().__init__(controller)

    def display(self, stdscr):
        self.stdscr = stdscr
        self.usernamebox = curses_helper.TextBox(stdscr, 6, 20, 20)
        self.passwordbox = curses_helper.TextBox(stdscr, 9, 20, 20)

        super().display(stdscr)

    def draw(self):
        self.stdscr.addstr(6, 20, self.controller.username)
        self.stdscr.addstr(9, 20, self.controller.password)
        super().draw()
        self.stdscr.move(6 + self.controller.cursor * 3, 20)

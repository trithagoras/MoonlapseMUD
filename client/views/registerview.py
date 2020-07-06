import curses

from ..curses_helper import TextBox
from .menuview import MenuView


class RegisterView(MenuView):
    def __init__(self, controller):
        self.username: str = ''
        self.password: str = ''
        self.confirmpassword: str = ''

        # Textboxes are initialised once the controller passes stdscr to the display method.
        self.usernamebox = None
        self.passwordbox = None
        self.confirmpasswordbox = None

        super().__init__(controller)

    def display(self, stdscr):
        self.stdscr = stdscr
        self.usernamebox = TextBox(stdscr, 6, 30, 20)
        self.passwordbox = TextBox(stdscr, 9, 30, 20)
        self.confirmpasswordbox = TextBox(stdscr, 12, 30, 20)

        super().display(stdscr)

    def draw(self):
        self.stdscr.addstr(6, 30, self.controller.username)
        self.stdscr.addstr(9, 30, self.controller.password)
        self.stdscr.addstr(12, 30, self.controller.confirmpassword)
        super().draw()
        self.stdscr.move(6 + self.controller.cursor * 3, 30)

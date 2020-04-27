import curses
from .controller import Controller
from ..views.menuview import MenuView

class Menu(Controller):
    def __init__(self, menu):
        super().__init__()
        self.menu = menu
        self.cursor: int = 0
        self.view = MenuView(self)

    def get_input(self) -> int:
        key = self.view.stdscr.getch()

        # Movement
        if key == curses.KEY_UP:
            self.cursor = max(self.cursor - 1, 0)
        elif key == curses.KEY_DOWN:
            self.cursor = min(self.cursor + 1, len(self.menu) - 1)
        elif key == curses.ascii.TAB:
            self.cursor = (self.cursor + 1) % len(self.menu)
        elif key in (curses.ascii.LF, curses.ascii.CR, curses.ascii.BEL, curses.KEY_ENTER):
            fn = self.menu[list(self.menu.keys())[self.cursor]]
            if fn is not None:
                fn()
        elif key == ord('q'):
            self.view.stop()

        return key

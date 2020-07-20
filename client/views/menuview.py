import curses
from curses_helper import color_addstr
from .view import View, Color


class MenuView(View):
    def __init__(self, controller, title: str = None):
        super().__init__(controller)
        self.title = title

    def draw(self) -> None:
        super().draw()
        for i, menuitem in enumerate(self.controller.menu.keys()):
            selected: bool = i == self.controller.cursor
            color_addstr(self.stdscr, 6 + i * 3, 5, menuitem, Color.WHITE, curses.A_BOLD if selected else curses.A_DIM)

        if self.title:
            color_addstr(self.stdscr, 2, (self.width - len(self.title)) // 2, self.title, Color.CYAN, curses.A_UNDERLINE)

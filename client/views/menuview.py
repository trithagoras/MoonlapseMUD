import curses

from .view import View


class MenuView(View):
    def __init__(self, controller, title: str = None):
        super().__init__(controller)
        self.title = title

    def draw(self) -> None:
        super().draw()
        for i, menuitem in enumerate(self.controller.menu.keys()):
            selected: bool = i == self.controller.cursor
            self.stdscr.addstr(6 + i * 3, 5, menuitem, curses.A_BOLD if selected else curses.A_DIM)

        if self.title:
            self.stdscr.addstr(2, (self.width - len(self.title)) // 2, self.title, curses.color_pair(2))

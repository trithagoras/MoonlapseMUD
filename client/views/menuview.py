import curses

from .view import View


class MenuView(View):
    def __init__(self, controller, title: str = None):
        super().__init__(controller)
        self.title = title

    def draw(self) -> None:
        super().draw()
        for i in range(len(self.controller.menu)):
            string = list(self.controller.menu.keys())[i]
            if i == self.controller.cursor:
                self.stdscr.addstr(6 + i * 3, 5, string, curses.A_UNDERLINE)
            else:
                self.stdscr.addstr(6 + i * 3, 5, string)

        if self.title is not None:
            self.stdscr.addstr(2, (self.width - len(self.title)) // 2, self.title, curses.color_pair(2))

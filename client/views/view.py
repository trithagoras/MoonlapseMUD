import curses
from . import Color
from curses_helper import color_addstr


class View:
    def __init__(self, controller):
        self.controller = controller

        # Init window sizes
        self.height, self.width = (41, 106)
        self.stdscr = None

        self.running = True

    def display(self, stdscr):
        self.stdscr = stdscr

        # Start colors in curses
        curses.start_color()

        # Init color pairs
        curses.init_pair(Color.WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(Color.CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(Color.RED, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(Color.GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(Color.MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(Color.YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(Color.BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)

        curses.curs_set(False)

        while self.running:
            self._update_display()

            try:
                self.controller.handle_input()
            except KeyboardInterrupt:
                self.controller.stop()
                self.stop()

    def _update_display(self):
        self.stdscr.erase()
        self.draw()
        self.stdscr.refresh()

    def draw(self) -> None:
        # Max terminal size
        if self.stdscr.getmaxyx() < (self.height, self.width):
            error: str = f"Window must be {self.height} rows x {self.width + 1} cols"
            color_addstr(self.stdscr, 0, (self.width - len(error)) // 2, error, Color.RED)

    def stop(self) -> None:
        self.running = False

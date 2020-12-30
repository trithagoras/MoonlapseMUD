import curses
from . import Color
from curses_helper import color_addstr
import time


class View:
    def __init__(self, controller):
        self.controller = controller

        # Init window sizes
        self.height, self.width = (41, 106)
        self.stdscr = None

        self.running = True

    def display(self, stdscr):
        self.stdscr = stdscr

        self.stdscr.keypad(True)

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
        if True:#try:
            self.draw()
            self.stdscr.refresh()
        # except Exception as e:
        #     error: str = f"Error: {e}"
        #     for ttl in range(3, 0, -1):
        #         self.stdscr.erase()
        #         hh: int = self.height // 2
        #         color_addstr(self.stdscr, hh, (self.width - len(error)) // 2, error, Color.RED)
        #         msg: str = f"Trying again in {ttl}"
        #         color_addstr(self.stdscr, hh + 1, (self.width - len(msg)) // 2, msg, Color.WHITE)
        #         self.stdscr.refresh()
        #         time.sleep(1)
        #     self._update_display()

    def draw(self) -> None:
        # Max terminal size
        if self.stdscr.getmaxyx() < (self.height, self.width):
            error: str = f"Window must be {self.height} rows x {self.width + 1} cols"
            color_addstr(self.stdscr, 0, (self.width - len(error)) // 2, error, Color.RED)

    def stop(self) -> None:
        self.running = False

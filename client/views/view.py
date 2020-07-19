import curses


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
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK)

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
            self.stdscr.addstr(0, (self.width - len(error)) // 2, error, curses.color_pair(4))

    def stop(self) -> None:
        self.running = False

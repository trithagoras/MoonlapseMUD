import curses

from client.controllers.widgets import Widget


class Window:
    def __init__(self, parent_win, y, x, height, width):
        self.y = y
        self.x = x
        self.height = height
        self.width = width
        self._win = parent_win.subwin(height, width, y, x)

    def border(self, color=None):
        if color:
            self._win.attron(curses.color_pair(color))
        self._win.border()
        if color:
            self._win.attroff(curses.color_pair(color))

    def title(self, s: str):
        self.addstr(0, 2, f"{s} ")

    def addstr(self, y: int, x: int, string: str, color=0, *attr):
        try:
            window = self._win
            window.attron(curses.color_pair(color))
            if attr:
                window.attron(attr)
            window.addstr(y, x, string)
            if attr:
                window.attroff(attr)
            window.attroff(curses.color_pair(color))
        except Exception as e:
            pass


class View:
    def __init__(self, controller):
        self.controller = controller

    def start(self):
        pass

    def _draw(self):
        stdscr = self.controller.cs.stdscr
        min_height, min_width = self.controller.cs.window.height, self.controller.cs.window.width
        term_height, term_width = stdscr.getmaxyx()

        try:
            self.controller.cs.stdscr.erase()
            self.draw()
            self.controller.debug.draw()
            if (term_height, term_width) < (min_height, min_width):
                raise Exception(f"Screen dimensions must be {min_height} rows x {min_width} cols (detected {term_height} x {term_width})")
            self.controller.cs.stdscr.refresh()

        except Exception as e:
            error: str = f"Error: {e}"
            for ttl in range(3, 0, -1):
                stdscr.erase()
                # TODO: Resizing the terminal on Windows won't change the value of stdscr.getmaxyx()
                # See:https://stackoverflow.com/questions/55554703/python-curses-getmaxyx-always-returning-same-value-on-windows
                # The following commented out part does not work
                # if curses.is_term_resized(term_height, term_width):
                #     term_height, term_width = stdscr.getmaxyx()
                #     curses.resizeterm(term_height, term_width)

                hh: int = term_height // 2
                self.addstr(hh, (term_width - len(error)) // 2, error, curses.COLOR_RED)
                msg: str = f"Trying again in {ttl}"
                self.addstr(hh + 1, (term_width - len(msg)) // 2, msg)
                stdscr.refresh()
                curses.napms(1000)

            self._draw()

    def draw(self):
        pass

    def stop(self):
        pass

    def place_widget(self, widget: Widget, y: int, x: int):
        widget.y = y
        widget.x = x
        pass

    def addstr(self, y: int, x: int, string: str, color=0, *attr):
        try:
            window = self.controller.cs.stdscr
            window.attron(curses.color_pair(color))
            if attr:
                window.attron(attr)
            window.addstr(y, x, string)
            if attr:
                window.attroff(attr)
            window.attroff(curses.color_pair(color))
        except Exception as e:
            pass

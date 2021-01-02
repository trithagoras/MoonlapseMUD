import curses
import time

from client.controllers.widgets import Widget


class Window:
    def __init__(self, parent_win, y, x, height, width):
        self.y = y
        self.x = x
        self.height = height
        self.width = width
        self._win = parent_win.subwin(height, width, y, x)

    def border(self):
        self._win.border()

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
        try:
            cs = self.controller.cs
            if cs.stdscr.getmaxyx() < (cs.window.height, cs.window.width):
                raise Exception(f"Screen dimensions must be {cs.window.height} rows x {cs.window.width} cols")

            self.controller.cs.stdscr.erase()
            self.draw()
            self.controller.cs.stdscr.refresh()
        except Exception as e:
            error: str = f"Error: {e}"
            for ttl in range(3, 0, -1):
                stdscr = self.controller.cs.stdscr
                height, width = stdscr.getmaxyx()
                stdscr.erase()
                hh: int = height // 2
                self.addstr(hh, (width - len(error)) // 2, error, curses.COLOR_RED)
                msg: str = f"Trying again in {ttl}"
                self.addstr(hh + 1, (width - len(msg)) // 2, msg)
                stdscr.refresh()
                time.sleep(1)
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

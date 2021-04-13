import curses
import curses.ascii
from . import keybindings


class Widget:
    """
    Interactable components in a view. i.e. TextField
    """

    def __init__(self, controller, hidden=False, disabled=False):
        self.controller = controller
        self.y = 0
        self.x = 0
        self.hidden = hidden
        self.disabled = disabled       # visible, but not interactable
        self.selected = False       # can interact with once True

    def select(self):
        self.selected = True

    def draw(self):
        if self.hidden:
            return

    def process_input(self, key: int):
        pass


class Button(Widget):
    def __init__(self, controller, text, action, *params):
        super().__init__(controller)
        self.text = text
        self.action = action
        self.params = params

    def draw(self):
        super().draw()
        self.controller.cs.stdscr.addstr(self.y, self.x, self.text)

    def select(self):
        self.action(*self.params)


class CheckBox(Widget):
    def __init__(self, controller, text="", checked=False):
        super().__init__(controller)
        self.text = text
        self.checked = checked

    def draw(self):
        super().draw()
        self.controller.cs.stdscr.addstr(self.y, self.x, self.text + (" [ ]" if not self.checked else " [X]"))

    def select(self):
        self.checked = not self.checked


class TextField(Widget):
    def __init__(self, controller, title="", initial_value="", max_length=32, censored=False, hidden=False, disabled=False):
        super().__init__(controller, hidden=hidden, disabled=disabled)
        self.title = title
        self.value = initial_value
        self.max_length = max_length
        self.censored = censored
        self.cursor = 0

    def draw(self):
        super().draw()
        window = self.controller.cs.window

        y = self.y
        x = self.x

        if self.title:
            window.addstr(self.y, self.x, self.title)
            x = self.x + len(self.title)

        if self.censored:
            window.addstr(y, x, "*" * len(self.value))
        else:
            window.addstr(y, x, self.value)

        if self.selected:
            value = " "
            # cursor pos
            if self.cursor == len(self.value):
                pass
            else:
                value = self.value[self.cursor]
                if self.censored:
                    value = "*"

            self.controller.view.addstr(y, x + self.cursor, value, curses.COLOR_WHITE)

    def process_input(self, key: int):
        if curses.ascii.isprint(key):
            if len(self.value) == self.max_length:
                return

            self.value = self.value[:self.cursor] + chr(key) + self.value[self.cursor:]
            self.cursor += 1
        elif key == curses.ascii.ESC:
            self.process_exit()
        elif keybindings.enter(key):
            self.process_submit()
        elif keybindings.backspace(key) and self.cursor > 0:  # press backspace
            self.value = self.value[:self.cursor - 1] + self.value[self.cursor:]
            self.cursor = max(self.cursor - 1, 0)
        elif key == curses.KEY_LEFT:
            self.cursor = max(self.cursor - 1, 0)
        elif key == curses.KEY_RIGHT:
            self.cursor = min(self.cursor + 1, len(self.value))
        elif key in [curses.KEY_UP, curses.KEY_DOWN, curses.ascii.TAB]:
            self.process_exit()
            self.controller.process_input(key)

    def process_exit(self):
        # if escape is pressed
        self.selected = False

    def process_submit(self):
        # if enter is pressed
        self.selected = False

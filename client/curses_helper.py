import curses
import curses.textpad
import curses.ascii
from typing import *
from client.views import Color


def color_addch(window, y: int, x: int, ch: chr, colour: int, *attr):
    window.attron(curses.color_pair(colour))
    if attr:
        window.attron(*attr)
    window.addch(y, x, ch)
    if attr:
        window.attroff(*attr)
    window.attron(curses.color_pair(Color.WHITE))


def color_addstr(window, y: int, x: int, string: str, colour: int, *attr):
    window.attron(curses.color_pair(colour))
    if attr:
        window.attron(*attr)
    window.addstr(y, x, string)
    if attr:
        window.attroff(*attr)
    window.attron(curses.color_pair(Color.WHITE))


def validator(key: int):
    if curses.ascii.isprint(key):
        return key

    # Delete left
    if key in (curses.ascii.BS, curses.KEY_BACKSPACE, curses.ascii.DEL):
        return curses.ascii.BS

    # Delete right
    if key in (curses.ascii.EOT, curses.KEY_DC):
        return curses.ascii.EOT

    # Stop editing
    if key in (curses.ascii.LF, curses.ascii.CR, curses.ascii.BEL, curses.KEY_ENTER, curses.ascii.ESC,
               curses.ascii.TAB, curses.KEY_DOWN, curses.KEY_UP):
        return curses.ascii.BEL

    return key


class TextBox:
    """
    A wrapper for the curses.Textpad.Textbox class (https://docs.python.org/2.0/lib/curses-textpad-objects.html)
    The main difference here is the inclusion of a custom validator for the editing process. It should also be 
    pretty cross platform in terms of input.
    """

    def __init__(self, parent_window, y: int, x: int, width: int, censored=False, parentview=None, wins_to_update: Iterable = None):
        """
        Initialises the TextBox.

        :param parent_window: The window whose upper-left corner defines the origin for this TextBox. This TextBox will
                              be contained in the parent window and displayed on top of it.
        :param y: The y-coordinate of the origin of this TextBox defined relative to the parent window 
                  (i.e. (y, x) == (0, 0) means this TextBox will share its origin with the parent window's).
        :param x: The x-coordinate of the origin of this TextBox defined relative to the parent window 
                  (i.e. (y, x) == (0, 0) means this TextBox will share its origin with the parent window's).
        :param width: The width/length of this TextBox. It is assumed to be such that this TextBox does not 
                      not overfill the parent window with the given x-coordinate of the origin. 
        """

        # Create a derived window for this TextBox (the same as a subwindow except y and x are relative to 
        # the origin of the parent rather than the entire screen)
        self.win = parent_window.derwin(1, width, y, x)

        self.censored = censored

        # Enable escape sequences to be handled by curses rather than interpreted by this TextBox
        self.win.keypad(1)

        # Define the underlying Textbox and enable spaces to be stripped from the result
        self.box: ExtendedTextBox = ExtendedTextBox(self.win, self.censored)

        self.value: str = ''

        # Editing the textbox is blocking, so we might need to supply some windows needing updating
        # each cycle through the edit loop.
        self.parentview = parentview
        self.wins_to_update = wins_to_update

    def modal(self, first_key: Optional[int] = None) -> None:
        """
        Enters the editing loop for this TextBox. This sets the result of this TextBox which can be 
        obtained with the get_value function.
        :param first_key: An optional first input key which can be passed in. This is useful if this 
                          modal is triggered by hitting an input character which you would like to be 
                          considered input to the TextBox (e.g. typing the first letter of a username).
        """
        self.win.clear()
        self.win.move(0, 0)
        curs_x = self.win.getyx()[1]

        curses.curs_set(1)

        if first_key is not None:
            if curses.ascii.isprint(first_key):
                # Add first letter and move cursor right
                if self.censored:
                    self.win.addch(0, curs_x, '*')
                else:
                    self.win.addch(0, curs_x, chr(first_key))
                self.value = chr(first_key)
                curs_x += 1
            elif first_key == curses.KEY_DC and len(self.value) > 0:
                # Delete first letter and move cursor at beginning
                self.win.addstr(0, 0, self.value[1:])
                curs_x = self.win.getyx()[1]
            elif first_key == curses.KEY_LEFT:
                # Move cursor left
                curs_x = max(0, curs_x - 1)

            self.win.move(self.win.getyx()[0], curs_x)

        self.box.value = self.value
        self.value = self.box.edit(validator, parentview=self.parentview, wins_to_update=self.wins_to_update)
        # I'm not sure why, but sometimes the value has a trailing space
        if len(self.value) > 0 and self.value[-1] == ' ':
            self.value = self.value[: -1]

        curses.curs_set(0)

    def display_value(self):
        if self.censored:
            return '*' * len(self.value)
        else:
            return self.value


class ExtendedTextBox(curses.textpad.Textbox):
    def __init__(self, win, censored):
        super().__init__(win)
        self.censored = censored
        self.value = ''

    def _insert_printable_char(self, ch):
        self._update_max_yx()
        (y, x) = self.win.getyx()
        backyx = None
        while y < self.maxy or x < self.maxx:
            if self.insert_mode:
                oldch = self.win.inch()
            # The try-catch ignores the error we trigger from some curses
            # versions by trying to write into the lowest-rightmost spot
            # in the window.
            try:
                if self.censored:
                    self.win.addch('*')
                else:
                    self.win.addch(ch)
            except curses.error:
                pass
            if not self.insert_mode or not curses.ascii.isprint(oldch):
                break
            ch = oldch
            (y, x) = self.win.getyx()
            # Remember where to put the cursor back since we are in insert_mode
            if backyx is None:
                backyx = y, x

        if backyx is not None:
            self.win.move(*backyx)

    def do_command(self, ch):
        "Process a single editing command."
        self._update_max_yx()
        (y, x) = self.win.getyx()
        self.lastcmd = ch
        if curses.ascii.isprint(ch):
            if y < self.maxy or x < self.maxx:
                self._insert_printable_char(ch)
                self.value += chr(ch)
        elif ch == curses.ascii.SOH:                           # ^a
            self.win.move(y, 0)
        elif ch in (curses.ascii.STX,curses.KEY_LEFT, curses.ascii.BS,curses.KEY_BACKSPACE):
            if x > 0:
                self.win.move(y, x-1)
            elif y == 0:
                pass
            elif self.stripspaces:
                self.win.move(y-1, self._end_of_line(y-1))
            else:
                self.win.move(y-1, self.maxx)
            if ch in (curses.ascii.BS, curses.KEY_BACKSPACE):
                self.value = self.value[:-1]
                self.win.delch()
        elif ch == curses.ascii.EOT:                           # ^d
            self.value = self.value[:-1]
            self.win.delch()
        elif ch == curses.ascii.ENQ:                           # ^e
            if self.stripspaces:
                self.win.move(y, self._end_of_line(y))
            else:
                self.win.move(y, self.maxx)
        elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):       # ^f
            if x < self.maxx:
                self.win.move(y, x+1)
            elif y == self.maxy:
                pass
            else:
                self.win.move(y+1, 0)
        elif ch == curses.ascii.BEL:                           # ^g
            return 0
        elif ch == curses.ascii.NL:                            # ^j
            if self.maxy == 0:
                return 0
            elif y < self.maxy:
                self.win.move(y+1, 0)
        elif ch == curses.ascii.VT:                            # ^k
            if x == 0 and self._end_of_line(y) == 0:
                self.value = ''
                self.win.deleteln()
            else:
                # first undo the effect of self._end_of_line
                self.win.move(y, x)
                self.win.clrtoeol()
        elif ch == curses.ascii.FF:                            # ^l
            self.win.refresh()
        elif ch in (curses.ascii.SO, curses.KEY_DOWN):         # ^n
            if y < self.maxy:
                self.win.move(y+1, x)
                if x > self._end_of_line(y+1):
                    self.win.move(y+1, self._end_of_line(y+1))
        elif ch == curses.ascii.SI:                            # ^o
            self.win.insertln()
        elif ch in (curses.ascii.DLE, curses.KEY_UP):          # ^p
            if y > 0:
                self.win.move(y-1, x)
                if x > self._end_of_line(y-1):
                    self.win.move(y-1, self._end_of_line(y-1))
        return 1

    def edit(self, validate=None, parentview=None, wins_to_update: Iterable = None):
        """Edit in the widget window and collect the results. Also updates any windows passed in to it each cycle."""
        self.win.nodelay(True)
        while 1:
            curses.curs_set(1)
            ch = self.win.getch()
            if validate:
                ch = validate(ch)
            if not ch:
                continue
            if not self.do_command(ch):
                break
            if wins_to_update:
                for win in wins_to_update:
                    win.erase()
                    parentview.draw()
                    curses.curs_set(0)
                    win.refresh()
            self.win.refresh()
        self.win.nodelay(False)
        return self.value

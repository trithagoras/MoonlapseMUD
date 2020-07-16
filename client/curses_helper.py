import curses.textpad
import curses.ascii
from typing import *


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

    def __init__(self, parent_window, y: int, x: int, width: int, parentview=None, wins_to_update: Iterable = None):
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

        # Enable escape sequences to be handled by curses rather than interpreted by this TextBox
        self.win.keypad(1)

        # Define the underlying Textbox and enable spaces to be stripped from the result
        self.box: ExtendedTextBox = ExtendedTextBox(self.win)

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
                self.win.addch(0, curs_x, chr(first_key))
                curs_x += 1
            elif first_key == curses.KEY_DC and len(self.value) > 0:
                # Delete first letter and move cursor at beginning
                self.win.addstr(0, 0, self.value[1:])
                curs_x = self.win.getyx()[1]
            elif first_key == curses.KEY_LEFT:
                # Move cursor left
                curs_x = max(0, curs_x - 1)

            self.win.move(self.win.getyx()[0], curs_x)

        self.value = self.box.edit(validator, parentview=self.parentview, wins_to_update=self.wins_to_update)
        # I'm not sure why, but sometimes the value has a trailing space
        if len(self.value) > 0 and self.value[-1] == ' ':
            self.value = self.value[: -1]

        curses.curs_set(0)


class ExtendedTextBox(curses.textpad.Textbox):
    def edit(self, validate=None, parentview=None, wins_to_update: Iterable = None):
        "Edit in the widget window and collect the results. Also updates any windows passed in to it each cycle."
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
        return self.gather()

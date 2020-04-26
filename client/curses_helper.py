import curses.textpad
import curses.ascii
from typing import *


class TextBox:
    """
    A wrapper for the curses.Textpad.Textbox class (https://docs.python.org/2.0/lib/curses-textpad-objects.html)
    The main difference here is the inclusion of a custom validator for the editing process.
    """

    def __init__(self, parent_window, y: int, x: int, width: int):
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
        self.box: curses.textpad.Textbox = curses.textpad.Textbox(self.win)

        self.value: str = ''

    def __del__(self):
        self.box = None
        self.win = None

    def modal(self, first_key: Optional[int] = None) -> None:
        """
        Enters the editing loop for this TextBox. This sets the result of this TextBox which can be 
        obtained with the get_value function.
        :param first_key: An optional first input key which can be passed in. This is useful if this 
                          modal is triggered by hitting an input character which you would like to be 
                          considered input to the TextBox (e.g. typing the first letter of a username).
        """
        self.win.move(0, len(self.value))
        curs_x = self.win.getyx()[1]

        if first_key is not None:
            if curses.ascii.isprint(first_key):
                # Add first letter and move cursor right
                self.win.addch(0, curs_x, chr(first_key))
                self.win.move(0, curs_x + 1)
            elif first_key == curses.KEY_DC and len(self.value) > 0:
                # Delete first letter and move cursor at beginning
                self.win.addstr(0, 0, self.value[1:])
                self.win.move(0, 0)
            elif first_key == curses.KEY_LEFT:
                # Move cursor left
                self.win.move(0, curs_x - 1)

        self.value = self.box.edit(self.validator)
        # I'm not sure why, but sometimes the value has a trailing space
        if self.value[-1] == ' ':
            self.value = self.value[: -1]

    def validator(self, key: int):
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

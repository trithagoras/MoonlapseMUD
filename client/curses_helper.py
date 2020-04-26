import curses.textpad
import curses.ascii
from typing import *


class TextBox:
    """
    A wrapper for the curses.Textpad.Textbox class (https://docs.python.org/2.0/lib/curses-textpad-objects.html)
    The main difference here is the inclusion of a custom validator for the editing process.
    """

    def __init__(self, parent_window: curses.window, y: int, x: int, width: int):
        """
        Initialises the TextBox.

        :param parent_window: The window whose upper-left corner defines the origin for this TextBox which 
                              This TextBox will be contained in the parent window and displayed on top of it.
        :param y: The y-coordinate of the origin of this TextBox defined relative to the parent window 
                  (i.e. (y, x) == (0, 0) means this TextBox will share its origin with the parent window's).
        :param x: The x-coordinate of the origin of this TextBox defined relative to the parent window 
                   (i.e. (y, x) == (0, 0) means this TextBox will share its origin with the parent window's).
        :param width: The width/length of this TextBox. It is assumed to be such that this TextBox does not 
                      not overfill the parent window with the given x-coordinate of the origin. 
        """

        # Create a derived window for this TextBox (the same as a subwindow except y and x are relative to 
        # the origin of the parent rather than the entire screen)
        self.win: curses.window = parent_window.derwin(1, width, y, x)

        # Enable escape sequences to be handled by curses rather than interpreted by this TextBox
        self.win.keypad(1)


        # Define the underlying Textbox and enable spaces to be stripped from the result
        self.box: curses.textpad.Textbox = curses.textpad.Textbox(self.win)
        self.box.stripspaces = True


        self.value: str = ''
        self.result: int = None
        self.editing = False

    def __del__(self):
        self.box = None
        self.win = None

    def modal(self, first_key: Optional[chr] = None) -> chr:
        """
        Enters the editing loop for this TextBox. This sets the result of this TextBox which can be 
        obtained with the get_value function.
        :param first_key: An optional first input key which can be passed in. This is useful if this 
                          modal is triggered by hitting an input character which you would like to be 
                          considered input to the TextBox (e.g. typing the first letter of a username).
        :return: 
        """
        self.win.clear()
        self.win.move(0, 0)
        if curses.ascii.isprint(first_key):
            first_key = chr(first_key)
            self.win.addch(0, 0, first_key)
            self.win.move(0, 1)
        
        self.editing = True
        self.value = self.box.edit(self.validator)
        self.editing = False
        return self.result

    def validator(self, char):
        """here we tweak the behavior slightly, especially we want to
        end modal editing mode immediately on arrow up/down and on enter
        and we also want to catch ESC and F10, to abort the entire dialog"""
        if curses.ascii.isprint(char):
            return char

        # Tab to move down
        if char == curses.ascii.TAB:
            return curses.KEY_DOWN

        # Linefeed, carriage return, enter, etc.
        if char in [curses.ascii.LF, curses.ascii.CR, curses.ascii.BEL, curses.KEY_ENTER]:
            return curses.ascii.BEL

        # Backspace, delete, etc.
        if char in (curses.ascii.BS, curses.KEY_BACKSPACE):
            return curses.ascii.BS

        if char in (curses.ascii.DEL, curses.ascii.EOT, curses.KEY_DC):
            return curses.ascii.EOT

        # Escape, F10, etc.
        if char in [curses.ascii.ESC, curses.KEY_F10]:
            return curses.ascii.BEL

        return char

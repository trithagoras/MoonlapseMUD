import curses.textpad
import curses.ascii
from typing import *


class TextBox:
    """wrapper for curses.textpad.Textbox"""

    def __init__(self, parent_window, posy, posx, length):
        self.parent_window = parent_window
        self.posy = posy
        self.posx = posx
        self.win = parent_window.derwin(1, length, posy, posx)
        self.win = parent_window.derwin(1, length, posy, posx)
        self.win.keypad(1)
        self.box = curses.textpad.Textbox(self.win, insert_mode=True)
        self.value = ''
        self.result = None
        self.editing = False

    def __del__(self):
        self.box = None
        self.win = None

    def modal(self, first_key: Optional[chr] = None):
        """enter the edit box modal loop"""
        self.win.move(0, 0)
        if first_key is not None:
            self.win.addch(0, 0, first_key)
        self.editing = True
        self.value = self.box.edit(self.validator).strip()
        self.editing = False
        return self.result

    def validator(self, char):
        """here we tweak the behavior slightly, especially we want to
        end modal editing mode immediately on arrow up/down and on enter
        and we also want to catch ESC and F10, to abort the entire dialog"""
        if curses.ascii.isprint(char):
            return char
        if char == curses.ascii.TAB:
            return curses.KEY_DOWN
        if char in [curses.KEY_DOWN, curses.KEY_UP]:
            self.result = char
            return curses.ascii.BEL
        if char in [10, 13, curses.KEY_ENTER, curses.ascii.BEL]:
            self.result = 10
            return curses.ascii.BEL
        if char == 127:
            return 8
        if char in [27, curses.KEY_F10]:
            self.result = -1
            return curses.ascii.BEL
        return char

import curses.ascii


def backspace(k):
    return k in (curses.ascii.BS, curses.KEY_BACKSPACE, curses.ascii.DEL)

def enter(k):
    return k in (curses.ascii.LF, curses.ascii.CR, curses.ascii.BEL, curses.KEY_ENTER)

def escape(k):
    return k in (curses.ascii.ESC, 27)
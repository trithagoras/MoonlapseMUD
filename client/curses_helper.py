from typing import *
import curses


# https://docs.python.org/3/library/curses.html#module-curses

class Curses:
    ERR = curses.ERR
    OK = curses.OK
    version = curses.version

    # attributes
    A_ALTCHARSET = curses.A_ALTCHARSET
    A_BLINK = curses.A_BLINK
    A_BOLD = curses.A_BOLD
    A_DIM = curses.A_DIM
    A_INVIS = 0
    A_ITALIC = 0
    A_NORMAL = 0
    A_PROTECT = 0
    A_REVERSE = 0
    A_STANDOUT = 0
    A_UNDERLINE = 0
    A_HORIZONTAL = 0
    A_LEFT = 0
    A_LOW = 0
    A_RIGHT = 0
    A_TOP = 0
    A_VERTICAL = 0
    A_CHARTEXT = 0

    A_ATTRIBUTES = 0
    A_COLOR = 0

    # colors
    COLOR_BLACK = 0
    COLOR_BLUE = 0
    COLOR_CYAN = 0
    COLOR_GREEN = 0
    COLOR_MAGENTA = 0
    COLOR_RED = 0
    COLOR_WHITE = 0
    COLOR_YELLOW = 0

    # keys
    KEY_MIN = 0
    KEY_BREAK = 0
    KEY_DOWN = 0
    KEY_UP = 0
    KEY_LEFT = 0
    KEY_RIGHT = 0
    KEY_HOME = 0
    KEY_BACKSPACE = 0
    KEY_F0 = 0
    KEY_Fn = 0
    KEY_DL = 0
    KEY_DC = 0
    KEY_IC = 0
    KEY_EIC = 0
    KEY_CLEAR = 0
    KEY_EOS = 0
    KEY_EOL = 0
    KEY_SF = 0
    KEY_SR = 0
    KEY_NPAGE = 0
    KEY_PPAGE = 0
    KEY_STAB = 0
    KEY_CTAB = 0
    KEY_CATAB = 0
    KEY_ENTER = 0
    KEY_RESET = 0
    KEY_PRINT = 0
    KEY_LL = 0
    KEY_A1 = 0
    KEY_A3 = 0
    KEY_B2 = 0
    KEY_C1 = 0
    KEY_C3 = 0
    KEY_BTAB = 0
    KEY_BEG = 0
    KEY_CANCEL = 0
    KEY_CLOSE = 0
    KEY_COMMAND = 0
    KEY_COPY = 0
    KEY_CREATE = 0
    KEY_END = 0
    KEY_EXIT = 0
    KEY_FIND = 0
    KEY_HELP = 0
    KEY_MARK = 0
    KEY_MESSAGE = 0
    KEY_MOVE = 0
    KEY_NEXT = 0
    KEY_OPEN = 0
    KEY_OPTIONS = 0
    KEY_PREVIOUS = 0
    KEY_REDO = 0
    KEY_REFERENCE = 0
    KEY_REFRESH = 0
    KEY_REPLACE = 0
    KEY_RESTART = 0
    KEY_RESUME = 0
    KEY_SAVE = 0
    KEY_SBEG = 0
    KEY_SCANCEL = 0
    KEY_SCOMMAND = 0
    KEY_SCOPY = 0
    KEY_SCREATE = 0
    KEY_SDC = 0
    KEY_SDL = 0
    KEY_SELECT = 0
    KEY_SEND = 0
    KEY_SEOL = 0
    KEY_SEXIT = 0
    KEY_SFIND = 0
    KEY_SHELP = 0
    KEY_SHOME = 0
    KEY_SIC = 0
    KEY_SLEFT = 0
    KEY_SMESSAGE = 0
    KEY_SMOVE = 0
    KEY_SNEXT = 0
    KEY_SOPTIONS = 0
    KEY_SPREVIOUS = 0
    KEY_SPRINT = 0
    KEY_SREDO = 0
    KEY_SREPLACE = 0
    KEY_SRIGHT = 0
    KEY_SRSUME = 0
    KEY_SSAVE = 0
    KEY_SSUSPEND = 0
    KEY_SUNDO = 0
    KEY_SUSPEND = 0
    KEY_UNDO = 0
    KEY_MOUSE = 0
    KEY_RESIZE = 0
    KEY_MAX = 0

    # only available after initscr() is called
    ACS_BBSS = 0
    ACS_BLOCK = 0
    ACS_BOARD = 0
    ACS_BSBS = 0
    ACS_BSSB = 0
    ACS_BSSS = 0
    ACS_BTEE = 0
    ACS_BULLET = 0
    ACS_CKBOARD = 0
    ACS_DARROW = 0
    ACS_DEGREE = 0
    ACS_DIAMOND = 0
    ACS_GEQUAL = 0
    ACS_HLINE = 0
    ACS_LANTERN = 0
    ACS_LARROW = 0
    ACS_LEQUAL = 0
    ACS_LLCORNER = 0
    ACS_LRCORNER = 0
    ACS_LTEE = 0
    ACS_NEQUAL = 0
    ACS_PI = 0
    ACS_PLMINUS = 0
    ACS_PLUS = 0
    ACS_RARROW = 0
    ACS_RTEE = 0
    ACS_S1 = 0
    ACS_S3 = 0
    ACS_S7 = 0
    ACS_S9 = 0
    ACS_SBBS = 0
    ACS_SBSB = 0
    ACS_SBSS = 0
    ACS_SSSB = 0
    ACS_SSSS = 0
    ACS_STERLING = 0
    ACS_TTEE = 0
    ACS_UARROW = 0
    ACS_ULCORNER = 0
    ACS_URCORNER = 0
    ACS_VLINE = 0

    @staticmethod
    def baudrate():
        pass
        
    @staticmethod
    def beep():
        pass
    
    @staticmethod
    def can_change_color():
        pass
    
    @staticmethod
    def cbreak():
        pass
    
    @staticmethod
    def color_content(color_number):
        pass
    
    @staticmethod
    def color_pair(color_number):
        pass
    
    @staticmethod
    def curs_set(visibility):
        pass
    
    @staticmethod
    def def_prog_mode():
        pass
    
    @staticmethod
    def def_shell_mode():
        pass
    
    @staticmethod
    def delay_output(ms):
        pass
    
    @staticmethod
    def doupdate():
        pass
    
    @staticmethod
    def echo():
        pass
    
    @staticmethod
    def endwin():
        pass
    
    @staticmethod
    def erasechar():
        pass
    
    @staticmethod
    def filter():
        pass
    
    @staticmethod
    def flash():
        pass
    
    @staticmethod
    def flushinp():
        pass
    
    @staticmethod
    def getmouse():
        pass
    
    @staticmethod
    def getsyx():
        pass
    
    @staticmethod
    def getwin(file):
        pass
    
    @staticmethod
    def has_colors():
        pass
    
    @staticmethod
    def has_ic():
        pass
    
    @staticmethod
    def has_il():
        pass
    
    @staticmethod
    def has_key(ch):
        pass
    
    @staticmethod
    def halfdelay(tenths):
        pass
    
    @staticmethod
    def init_color(color_number, r, g, b):
        pass
    
    @staticmethod
    def init_pair(pair_number, fg, bg):
        pass
    
    @staticmethod
    def initscr():
        pass
    
    @staticmethod
    def is_term_resized(nlines, ncols):
        pass
    
    @staticmethod
    def isendwin():
        pass
    
    @staticmethod
    def keyname(k):
        pass
    
    @staticmethod
    def killchar():
        pass
    
    @staticmethod
    def longname():
        pass
    
    @staticmethod
    def meta(flag):
        pass
    
    @staticmethod
    def mouseinterval(interval):
        pass
    
    @staticmethod
    def mousemask(mousemask):
        pass
    
    @staticmethod
    def napms(ms):
        pass
    
    @staticmethod
    def newpad(nlines, ncols):
        pass
    
    @staticmethod
    def newwin(nlines, ncols, begin_y=0, begin_x=0):
        pass
    
    @staticmethod
    def nl():
        pass
    
    @staticmethod
    def nocbreak():
        pass
    
    @staticmethod
    def noecho():
        pass
    
    @staticmethod
    def nonl():
        pass
    
    @staticmethod
    def noqiflush():
        pass
    
    @staticmethod
    def noraw():
        pass
    
    @staticmethod
    def pair_content(pair_number):
        pass
    
    @staticmethod
    def pair_number(attr):
        pass
    
    @staticmethod
    def putp(string):
        pass
    
    @staticmethod
    def qiflush(flag=None):
        pass
    
    @staticmethod
    def raw():
        pass
    
    @staticmethod
    def reset_prog_mode():
        pass
    
    @staticmethod
    def reset_shell_mode():
        pass
    
    @staticmethod
    def resetty():
        pass
    
    @staticmethod
    def resize_term(nlines, ncols):
        pass
    
    @staticmethod
    def resizeterm(nlines, ncols):
        pass
    
    @staticmethod
    def savetty():
        pass
    
    @staticmethod
    def setsyx(y, x):
        pass
    
    @staticmethod
    def setupterm(term=None, fd=-1):
        pass
    
    @staticmethod
    def start_color():
        pass
    
    @staticmethod
    def termattrs():
        pass
    
    @staticmethod
    def termname():
        pass
    
    @staticmethod
    def tigetflag(capname):
        pass
    
    @staticmethod
    def tigetnum(capname):
        pass
    
    @staticmethod
    def tigetstr(capname):
        pass
    
    @staticmethod
    def tparm(string, *args):
        pass
    
    @staticmethod
    def typeahead(fd):
        pass
    
    @staticmethod
    def unctrl(ch):
        pass
    
    @staticmethod
    def ungetch(ch):
        pass
    
    @staticmethod
    def update_lines_cols():
        pass
    
    @staticmethod
    def unget_wch(ch):
        pass
    
    @staticmethod
    def ungetmouse(id, x, y, z, bstate):
        pass
    
    @staticmethod
    def use_env(flag):
        pass
    
    @staticmethod
    def use_default_colors():
        pass
    
    @staticmethod
    def wrapper(func, *args):
        pass


"""
Window objects, as returned by initscr() and newwin(), have the following methods and attributes:
"""


class Window:
    """
    Paint character ch at (y, x) with attributes attr, overwriting any character previously painter at that location.
    By default, the character position and attributes are the current settings for the window object.
    """
    def addch(self, y, x, ch, attr=None) -> None:
        pass

    """
    Paint at most n characters of the character string str at (y, x) with attributes attr, overwriting 
    anything previously on the display.
    """
    def addnstr(self, y, x, string, n, attr=None) -> None:
        pass

    """
    Paint the character string str at (y, x) with attributes attr, overwriting anything previously on the display.
    """
    def addstr(self, y, x, string, attr=None) -> None:
        pass

    """
    Remove attribute attr from the “background” set applied to all writes to the current window.
    """
    def attroff(self, attr) -> None:
        pass

    """
    Add attribute attr from the “background” set applied to all writes to the current window.
    """
    def attron(self, attr) -> None:
        pass

    """
    Set the “background” set of attributes to attr. This set is initially 0 (no attributes).
    """
    def attrset(self, attr) -> None:
        pass

    """
    Set the background property of the window to the character ch, with attributes attr. The change is then applied 
    to every character position in that window:
    
    * The attribute of every character in the window is changed to the new background attribute.
    * Wherever the former background character appears, it is changed to the new background character.
    """
    def bkgd(self, ch, attr=None) -> None:
        pass

    """
    Set the window’s background. A window’s background consists of a character and any combination of attributes. 
    The attribute part of the background is combined (OR’ed) with all non-blank characters that are written into 
    the window. Both the character and attribute parts of the background are combined with the blank characters. 
    The background becomes a property of the character and moves with the character through any scrolling and 
    insert/delete line/character operations.
    """
    def bkgdset(self, ch, attr=None) -> None:
        pass

    """
    Draw a border around the edges of the window. Each parameter specifies the character to use for a specific part of 
    the border
    Note: 0 value for any parameter will cause the default character to be used for that parameter. Keyword 
    parameters can not be used.
    """
    def border(self, ls=0, rs=0, ts=0, bs=0, tl=0, tr=0, bl=0, br=0) -> None:
        pass

    """
    Similar to border(), but both ls and rs are vertch and both ts and bs are horch. The default corner characters 
    are always used by this function.
    """
    def box(self, vertch=0, horch=0) -> None:
        pass

    """
    Set the attributes of num characters at the current cursor position, or at position (y, x) if supplied. If num 
    is not given or is -1, the attribute will be set on all the characters to the end of the line. This function 
    moves cursor to position (y, x) if supplied. The changed line will be touched using the touchline() method so 
    that the contents will be redisplayed by the next window refresh.
    """
    def chgat(self, y, x, num, attr) -> None:
        pass

    """
    Like erase(), but also cause the whole window to be repainted upon next call to refresh().
    """
    def clear(self) -> None:
        pass

    """
    If flag is True, the next call to refresh() will clear the window completely.
    """
    def clearok(self, flag: bool) -> None:
        pass

    """
    Erase from cursor to the end of the window: all lines below the cursor are deleted, 
    and then the equivalent of clrtoeol() is performed.
    """
    def clrtobot(self) -> None:
        pass

    """
    Erase from cursor to the end of the line.
    """
    def clrtoeol(self) -> None:
        pass

    """
    Update the current cursor position of all the ancestors of the window to reflect the current cursor position of 
    the window.
    """
    def cursyncup(self) -> None:
        pass

    """
    Delete any character at (y, x).
    """
    def delch(self, y, x) -> None:
        pass

    """
    Delete the line under the cursor. All following lines are moved up by one line.
    """
    def deleteln(self) -> None:
        pass

    """
    An abbreviation for “derive window”, derwin() is the same as calling subwin(), except that begin_y and begin_x 
    are relative to the origin of the window, rather than relative to the entire screen. Return a window object 
    for the derived window.
    """
    def derwin(self, nlines, ncols, begin_y, begin_x) -> 'Window':
        pass

    """
    Add character ch with attribute attr, and immediately call refresh() on the window.
    """
    def echochar(self, ch, attr=None) -> None:
        pass

    """
    Test whether the given pair of screen-relative character-cell coordinates are enclosed by the given window, 
    returning True or False. It is useful for determining what subset of the screen windows enclose the location 
    of a mouse event.
    """
    def enclose(self, y, x) -> bool:
        pass

    """
    Encoding used to encode method arguments (Unicode strings and characters). The encoding attribute 
    is inherited from the parent window when a subwindow is created, for example with window.subwin(). 
    By default, the locale encoding is used (see locale.getpreferredencoding()).
    """
    encoding: int

    """
    Clear the window.
    """
    def erase(self) -> None:
        pass

    """
    Return a tuple (y, x) of co-ordinates of upper-left corner.
    """
    def getbegyx(self) -> Tuple[int, int]:
        pass

    """
    Return the given window’s current background character/attribute pair.
    """
    def getbkgd(self) -> Tuple[int, int]:
        pass

    """
    Get a character. Note that the integer returned does not have to be in ASCII range: function keys, 
    keypad keys and so on are represented by numbers higher than 255. In no-delay mode, return -1 if 
    there is no input, otherwise wait until a key is pressed.
    """
    def getch(self, y=0, x=0) -> int:
        pass

    """
    Get a wide character. Return a character for most keys, or an integer for function keys, keypad keys, 
    and other special keys. In no-delay mode, raise an exception if there is no input.
    """
    def getwch(self, y=0, x=0) -> int:
        pass

    """
    Get a character, returning a string instead of an integer, as getch() does. Function keys, keypad keys and 
    other special keys return a multibyte string containing the key name. In no-delay mode, raise an exception
    if there is no input.
    """
    def getkey(self, y=0, x=0) -> str:
        pass

    """
    Return a tuple (y, x) of the height and width of the window.
    """
    def getmaxyx(self) -> Tuple[int, int]:
        pass

    """
    Return the beginning coordinates of this window relative to its parent window as a tuple (y, x). 
    Return (-1, -1) if this window has no parent.
    """
    def getparyx(self) -> Tuple[int, int]:
        pass

    """
    Read a bytes object from the user, with primitive line editing capacity.
    """
    def getstr(self, y, x, n) -> bytes:
        pass

    """
    Return a tuple (y, x) of current cursor position relative to the window’s upper-left corner.
    """
    def getyx(self) -> Tuple[int, int]:
        pass

    """
    Display a horizontal line starting at (y, x) with length n consisting of the character ch.
    """
    def hline(self, y, x, ch, n) -> None:
        pass

    """
    If flag is False, curses no longer considers using the hardware insert/delete character feature of the 
    terminal; if flag is True, use of character insertion and deletion is enabled. When curses is first 
    initialized, use of character insert/delete is enabled by default.
    """
    def idcok(self, flag) -> None:
        pass

    """
    If flag is True, curses will try and use hardware line editing facilities. Otherwise, line insertion/deletion 
    are disabled.
    """
    def idlok(self, flag) -> None:
        pass

    """
    If flag is True, any change in the window image automatically causes the window to be refreshed; 
    you no longer have to call refresh() yourself. However, it may degrade performance considerably, due 
    to repeated calls to wrefresh. This option is disabled by default.
    """
    def immedok(self, flag) -> None:
        pass

    """
    Return the character at the given position in the window. The bottom 8 bits are the character proper, and 
    upper bits are the attributes.
    """
    def inch(self, y=0, x=0) -> chr:
        pass

    """
    Paint character ch at (y, x) with attributes attr, moving the line from position x right by one character.
    """
    def insch(self, y, x, ch, attr=None) -> None:
        pass

    """
    Insert nlines lines into the specified window above the current line. The nlines bottom lines are lost. 
    For negative nlines, delete nlines lines starting with the one under the cursor, and move the remaining 
    lines up. The bottom nlines lines are cleared. The current cursor position remains the same.
    """
    def insdelln(self, nlines) -> None:
        pass

    """
    Insert a blank line under the cursor. All following lines are moved down by one line.
    """
    def insertln(self) -> None:
        pass

    """
    Insert a character string (as many characters as will fit on the line) before the character under the cursor, 
    up to n characters. If n is zero or negative, the entire string is inserted. All characters to the right of 
    the cursor are shifted right, with the rightmost characters on the line being lost. The cursor position does 
    not change (after moving to y, x, if specified).
    """
    def insnstr(self, y, x, string, n, attr=None) -> None:
        pass

    """
    Insert a character string (as many characters as will fit on the line) before the character under the 
    cursor. All characters to the right of the cursor are shifted right, with the rightmost characters 
    on the line being lost. The cursor position does not change (after moving to y, x, if specified).
    """
    def insstr(self, y, x, string, attr=None) -> None:
        pass

    """
    Return a bytes object of characters, extracted from the window starting at the current 
    cursor position, or at y, x if specified. Attributes are stripped from the characters. If n is 
    specified, instr() returns a string at most n characters long (exclusive of the trailing NUL).
    """
    def instr(self, y, x, n=None) -> bytes:
        pass

    """
    Return True if the specified line was modified since the last call to refresh(); otherwise return False. 
    Raise a curses.error exception if line is not valid for the given window.
    """
    def is_linetouched(self, line) -> bool:
        pass

    """
    Return True if the specified window was modified since the last call to refresh(); otherwise return False.
    """
    def is_wintouched(self) -> bool:
        pass

    """
    If flag is True, escape sequences generated by some keys (keypad, function keys) will be interpreted by curses. 
    If flag is False, escape sequences will be left as is in the input stream.
    """
    def keypad(self, flag) -> None:
        pass

    """
    If flag is True, cursor is left where it is on update, instead of being at “cursor position.” 
    This reduces cursor movement where possible. If possible the cursor will be made invisible.

    If flag is False, cursor will always be at “cursor position” after an update.
    """
    def leaveok(self, flag) -> None:
        pass

    """
    Move cursor to (new_y, new_x).
    """
    def move(self, y, x) -> None:
        pass

    """
    Move the window inside its parent window. The screen-relative parameters of the window are not changed. 
    This routine is used to display different parts of the parent window at the same physical position on the screen.
    """
    def mvderwin(self, y, x) -> None:
        pass

    """
    Move the window so its upper-left corner is at (new_y, new_x).
    """
    def mvwin(self, y, x) -> None:
        pass

    """
    If flag is True, getch() will be non-blocking.
    """
    def nodelay(self, flag) -> None:
        pass

    """
    If flag is True, escape sequences will not be timed out.
    If flag is False, after a few milliseconds, an escape sequence will not be interpreted, and will be 
    left in the input stream as is.
    """
    def notimeout(self, flag) -> None:
        pass

    """
    Mark for refresh but wait. This function updates the data structure representing the desired state of the window, 
    but does not force an update of the physical screen. To accomplish that, call doupdate().
    """
    def noutrefresh(self) -> None:
        pass

    """
    Overlay the window on top of destwin. The windows need not be the same size, only the overlapping region is copied. 
    This copy is non-destructive, which means that the current background character does not overwrite the 
    old contents of destwin.
    
    To get fine-grained control over the copied region, the second form of overlay() can be used. 
    sminrow and smincol are the upper-left coordinates of the source window, and the other variables 
    mark a rectangle in the destination window.
    """
    def overlay(self, destwin, sminrow=0, smincol=0, dminrow=0, dmincol=0, dmaxrow=0, dmaxcol=0) -> None:
        pass

    """
    Overwrite the window on top of destwin. The windows need not be the same size, in which case only the 
    overlapping region is copied. This copy is destructive, which means that the current background character 
    overwrites the old contents of destwin.

    To get fine-grained control over the copied region, the second form of overwrite() can be used. 
    sminrow and smincol are the upper-left coordinates of the source window, the other variables mark a 
    rectangle in the destination window.
    """
    def overwrite(self, destwin, sminrow=0, smincol=0, dminrow=0, dmincol=0, dmaxrow=0, dmaxcol=0) -> None:
        pass

    """
    Write all data associated with the window into the provided file object. This information can be later 
    retrieved using the getwin() function.
    """
    def putwin(self, file) -> None:
        pass

    """
    Indicate that the num screen lines, starting at line beg, are corrupted and should be completely 
    redrawn on the next refresh() call.
    """
    def redrawln(self, beg, num) -> None:
        pass

    """
    Touch the entire window, causing it to be completely redrawn on the next refresh() call.
    """
    def redrawwin(self) -> None:
        pass

    """
    Update the display immediately (sync actual screen with previous drawing/deleting methods).

    The 6 optional arguments can only be specified when the window is a pad created with newpad(). 
    The additional parameters are needed to indicate what part of the pad and screen are involved. 
    pminrow and pmincol specify the upper left-hand corner of the rectangle to be displayed in the pad. 
    sminrow, smincol, smaxrow, and smaxcol specify the edges of the rectangle to be displayed on the screen. 
    The lower right-hand corner of the rectangle to be displayed in the pad is calculated from the screen 
    coordinates, since the rectangles must be the same size. Both rectangles must be entirely contained within 
    their respective structures. Negative values of pminrow, pmincol, sminrow, or smincol are treated as if 
    they were zero.
    """
    def refresh(self, pminrow=0, pmincol=0, sminrow=0, smincol=0, smaxrow=0, smaxcol=0) -> None:
        pass

    """
    Reallocate storage for a curses window to adjust its dimensions to the specified values. If either 
    dimension is larger than the current values, the window’s data is filled with blanks that have the 
    current background rendition (as set by bkgdset()) merged into them.
    """
    def resize(self, nlines, ncols) -> None:
        pass

    """
    Scroll the screen or scrolling region upward by lines lines.
    """
    def scroll(self, lines=1) -> None:
        pass

    """
    Control what happens when the cursor of a window is moved off the edge of the window or scrolling region, 
    either as a result of a newline action on the bottom line, or typing the last character of the last line. 
    If flag is False, the cursor is left on the bottom line. If flag is True, the window is scrolled up one line. 
    Note that in order to get the physical scrolling effect on the terminal, it is also necessary to call idlok().
    """
    def scrollok(self, flag) -> None:
        pass

    """
    Set the scrolling region from line top to line bottom. All scrolling actions will take place in this region.
    """
    def setscrreg(self, top, bottom) -> None:
        pass

    """
    Turn off the standout attribute. On some terminals this has the side effect of turning off all attributes.
    """
    def standend(self) -> None:
        pass

    """
    Turn on attribute A_STANDOUT.
    """
    def standout(self) -> None:
        pass

    """
    Return a sub-window, whose upper-left corner is at (begin_y, begin_x), and whose width/height is ncols/nlines.
    """
    def subpad(self, nlines, ncols, begin_y, begin_x) -> 'Window':
        pass

    """
    Return a sub-window, whose upper-left corner is at (begin_y, begin_x), and whose width/height is ncols/nlines.
    By default, the sub-window will extend from the specified position to the lower right corner of the window.
    """
    def subwin(self, nlines, ncols, begin_y, begin_x) -> 'Window':
        pass

    """
    Touch each location in the window that has been touched in any of its ancestor windows. This routine is 
    called by refresh(), so it should almost never be necessary to call it manually.
    """
    def syncdown(self) -> None:
        pass

    """
    If flag is True, then syncup() is called automatically whenever there is a change in the window.
    """
    def syncok(self, flag) -> None:
        pass

    """
    Touch all locations in ancestors of the window that have been changed in the window.
    """
    def syncup(self) -> None:
        pass

    """
    Set blocking or non-blocking read behavior for the window. If delay is negative, blocking read is used 
    (which will wait indefinitely for input). If delay is zero, then non-blocking read is used, and getch() 
    will return -1 if no input is waiting. If delay is positive, then getch() will block for delay milliseconds, 
    and return -1 if there is still no input at the end of that time.
    """
    def timeout(self, delay) -> None:
        pass

    """
    Pretend count lines have been changed, starting with line start. If changed is supplied, it specifies 
    whether the affected lines are marked as having been changed (changed=True) or unchanged (changed=False).
    """
    def touchline(self, start, count, changed=False) -> None:
        pass

    """
    Pretend the whole window has been changed, for purposes of drawing optimizations.
    """
    def touchwin(self) -> None:
        pass

    """
    Mark all lines in the window as unchanged since the last call to refresh().
    """
    def untouchwin(self) -> None:
        pass

    """
    Display a vertical line starting at (y, x) with length n consisting of the character ch.
    """
    def vline(self, y, x, ch, n) -> None:
        pass


"""
Panel objects, as returned by new_panel() above, are windows with a stacking order. There’s always a window associated 
with a panel which determines the content, while the panel methods are responsible for the window’s depth 
in the panel stack.
"""


class Panel:
    """
    Returns the panel above the current panel.
    """
    def above(self) -> 'Panel':
        pass

    """
    Returns the panel below the current panel.
    """
    def below(self) -> 'Panel':
        pass

    """
    Push the panel to the bottom of the stack.
    """
    def bottom(self) -> None:
        pass

    """
    Returns True if the panel is hidden (not visible), False otherwise.
    """
    def hidden(self) -> bool:
        pass

    """
    Hide the panel. This does not delete the object, it just makes the window on screen invisible.
    """
    def hide(self) -> None:
        pass

    """
    Move the panel to the screen coordinates (y, x).
    """
    def move(self, y, x) -> None:
        pass

    """
    Change the window associated with the panel to the window win.
    """
    def replace(self, win: Window) -> None:
        pass

    """
    Set the panel’s user pointer to obj. This is used to associate an arbitrary piece of data with the panel, and can 
    be any Python object.
    """
    def set_userptr(self, obj: object) -> None:
        pass

    """
    Display the panel (which might have been hidden).
    """
    def show(self) -> None:
        pass

    """
    Push panel to the top of the stack.
    """
    def top(self) -> None:
        pass

    """
    Returns the user pointer for the panel. This might be any Python object.
    """
    def userptr(self) -> object:
        pass

    """
    Returns the window object associated with the panel.
    """
    def window(self) -> Window:
        pass

import curses as ncurses
from curses import textpad
from typing import *

from curses_helper import Window, Curses
import time


class View:
    def __init__(self, controller):
        self.controller = controller

        # Init window sizes
        self.height, self.width = (43, 106)
        self.stdscr: Optional[Window] = None

        self.running = True

    def display(self, stdscr: Window):
        self.stdscr = stdscr

        # Start colors in curses
        ncurses.start_color()

        # Init color pairs
        ncurses.init_pair(1, ncurses.COLOR_WHITE, ncurses.COLOR_BLACK)
        ncurses.init_pair(2, ncurses.COLOR_BLACK, ncurses.COLOR_WHITE)
        ncurses.init_pair(3, ncurses.COLOR_CYAN, ncurses.COLOR_BLACK)
        ncurses.init_pair(4, ncurses.COLOR_RED, ncurses.COLOR_BLACK)
        ncurses.init_pair(5, ncurses.COLOR_GREEN, ncurses.COLOR_BLACK)
        ncurses.init_pair(6, ncurses.COLOR_MAGENTA, ncurses.COLOR_BLACK)

        while self.running:
            self.stdscr.erase()
            self.draw()
            self.stdscr.refresh()

            self.controller.get_input()

    def draw(self) -> None:
        # Max terminal size
        if self.stdscr.getmaxyx() < (self.height, self.width):
            self.stdscr.addstr(0, 0, f"Must be {self.height} rows x {self.width} cols")

    def stop(self) -> None:
        self.running = False


class MenuView(View):
    def __init__(self, controller, title: str = None):
        super().__init__(controller)
        self.title = title

    def draw(self) -> None:
        super().draw()
        for i in range(len(self.controller.menu)):
            string = list(self.controller.menu.keys())[i]
            if i == self.controller.cursor:
                string += ' *'
            self.stdscr.addstr(6 + i * 3, 5, string)

        if self.title is not None:
            self.stdscr.addstr(5, 5, self.title)


class LoginView(MenuView):
    def __init__(self, controller):
        self.username: str = ''
        self.password: str = ''
        super().__init__(controller)

    def display(self, stdscr: Window):
        self.win1: Window = stdscr.subwin(1, 20, 6, 20)
        self.win2: Window = stdscr.subwin(1, 20, 9, 20)

        self.usernamebox = textpad.Textbox(self.win1)
        self.passwordbox = textpad.Textbox(self.win2)

        super().display(stdscr)

    def draw(self):
        try:
            self.win1.addstr(0, 0, self.controller.username)
            self.win2.addstr(0, 0, self.controller.password)
        except ncurses.error as e:
            self.title = str(e)
        super().draw()
        self.stdscr.move(6 + self.controller.cursor * 3, 21)


class GameView(View):
    def __init__(self, game):
        super().__init__(game)

        self.game = game
        self.log: dict = {}
        self.log_latest: dict = {}

        self.win1_height, self.win1_width = (23, 53)
        self.win1_y, self.win1_x = (3, 0)
        self.win2_height, self.win2_width = (23, 53)
        self.win2_y, self.win2_x = (3, 53)
        self.win3_height, self.win3_width = (17, 106)
        self.win3_y, self.win3_x = (26, 0)
        self.chatwin_height, self.chatwin_width = (1, self.win3_width - 8)
        self.chatwin_y, self.chatwin_x = (self.win3_y + self.win3_height - self.chatwin_height - 1, self.win3_x + 7)

    def display(self, stdscr: Window):
        stdscr.timeout(round(1000 / self.game.tick_rate))

        # Init windows
        self.win1: Window = stdscr.subwin(self.win1_height, self.win1_width, self.win1_y, self.win1_x)
        self.win2: Window = stdscr.subwin(self.win2_height, self.win2_width, self.win2_y, self.win2_x)
        self.win3: Window = stdscr.subwin(self.win3_height, self.win3_width, self.win3_y, self.win3_x)
        self.chatwin: Window = stdscr.subwin(self.chatwin_height, self.chatwin_width, self.chatwin_y, self.chatwin_x)

        # Window 2 and focus
        self.focus = 1
        self.win2_focus = Window2Focus.SKILLS

        super().display(stdscr)

        # Position cursor
        self.stdscr.move(self.chatwin_y, self.chatwin_x)

    def draw(self) -> None:
        super().draw()

        # Focus control labels
        self.stdscr.hline(0, 0, ncurses.ACS_HLINE, self.width)

        control_title, control_string = "", ""
        if self.focus == 1:
            control_title = "Map Controls "
            control_string = "[V] Look  [D] Pick up item  [E] Use/Equip  [←/→/↑/↓] Move  [</>] Use Stairs/Ladders"
        elif self.focus == 2:
            control_title = f"{self.win2_focus[0]} Controls "
            control_string = f"{self.win2_focus[1]}"
        elif self.focus == 3:
            control_title = "Log Controls "
            control_string = "[A] Game  [G] Guild  [W] Whispers"

        self.stdscr.addstr(0, 2, control_title)
        self.stdscr.addstr(1, 2, control_string)

        # help key
        help_string = "[?] Help"
        self.stdscr.addstr(1, self.width - 1 - len(help_string), help_string)

        # Adding border to windows
        self.win1.border()
        self.win2.border()
        self.win3.border()

        # Rendering window titles
        if self.focus == 1:
            self.title(self.win1, "[1] Forgotten Moor", True)
        else:
            self.win1.addstr(0, 2, "[1] Forgotten Moor ")

        if self.focus == 2:
            self.title(self.win2, f"[2] {self.win2_focus[0]}", True)
        else:
            self.title(self.win2, f"[2] {self.win2_focus[0]}")

        if self.focus == 3:
            self.title(self.win3, "[3] Log", True)
        else:
            self.title(self.win3, "[3] Log")

        # Window 1 content
        for index in range(0, len(self.game.game_data['p'])):
            player = self.game.game_data['p'][index]

            if player is not None:
                self.win1.addch(player['pos']['y'] + 1, player['pos']['x'], player['c'])

        for wall in self.game.walls:
            self.win1.addch(wall[1] + 1, wall[0], '█')

        # Window 2 content
        if self.win2_focus == Window2Focus.SKILLS:
            self.status_win()
        elif self.win2_focus == Window2Focus.HELP:
            self.help_win()

        # Window 3 content
        self.win3.hline(self.win3_height - 3, 1, ncurses.ACS_HLINE, self.win3_width - 2)

        # Fill the log
        if self.game.game_data['l'] and self.game.game_data['l'] != self.log_latest:
            self.log.update(self.game.game_data['l'])
            self.log_latest = self.game.game_data['l']

        if self.log != {}:
            log_keys = list(self.log.keys())
            # Strip the old logs that can't fit in the window.
            log_keys = log_keys[max(0, len(log_keys) - self.win3_height + self.chatwin_height + 4):]

            log_line: int = 2
            for k in log_keys:
                timestamp: str = time.strftime('%R', time.localtime(float(k)))
                message: str = self.log[k]
                self.win3.addstr(log_line, 1, f" [{timestamp}] {message}")
                log_line += 1

        # Add chat prompt
        self.win3.addstr(15, 2, "Say: ")

    def help_win(self):
        self.win2.addstr(2, 2, "Navigating the 3 game panels can be done with the")
        self.win2.addstr(3, 2, "[1], [2], [3] keys.")
        self.win2.addstr(4, 2, "Controls for each focused panel is shown above.")

        self.win2.addstr(6, 2, "The second panel [2] can be changed to show")
        self.win2.addstr(7, 2, "other screens which can be focused and")
        self.win2.addstr(8, 2, "interacted with. The keys to do so are")
        self.win2.addstr(9, 2, "found in the help section below:")

        self.win2.addstr(11, 2, "[?] Help")
        self.win2.addstr(12, 2, "[K] Skills")
        self.win2.addstr(13, 2, "[I] Inventory")
        self.win2.addstr(14, 2, "[P] Spellbook")
        self.win2.addstr(15, 2, "[G] Guild / Social")
        self.win2.addstr(16, 2, "[J] Journal")

    def status_win(self):
        self.win2.addstr(1, 2, "coreyb65, Guardian of Forgotten Moor")
        self.win2.addstr(3, 2, f"Level 15 {self.progress_bar(7, 10)} (7/10 skill levels to 16)")

        self.win2.addstr(5, 2, f"Vitality      31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(6, 2, f"Strength      10/10 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(7, 2, f"Agility       31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(8, 2, f"Dexterity     31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(9, 2, f"Astrology     31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(10, 2, f"Intelligence  31/31 {self.progress_bar(3, 10)} (3,000/10,000)")

        self.win2.addstr(12, 2, f"Woodcutting   31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(13, 2, f"Crafting      31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(14, 2, f"Mining        31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(15, 2, f"Smithing      31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(16, 2, f"Fishing       31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(17, 2, f"Cooking       31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(18, 2, f"Alchemy       31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(19, 2, f"Enchanting    31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
        self.win2.addstr(20, 2, f"??????????    31/31 {self.progress_bar(3, 10)} (3,000/10,000)")

    @staticmethod
    def progress_bar(value: float, max_value: float) -> str:
        percent = int(10 * (value / max_value)) + 1

        s = "[-----------]"
        s = s[:percent] + "o" + s[percent + 1:]
        return s

    @staticmethod
    def title(window: Window, s: str, focus=False):
        if focus is False:
            window.addstr(0, 2, f"{s} ")
        else:
            window.addstr(0, 2, f"{s} ", ncurses.color_pair(3))


class Window2Focus:
    HELP = ["Help", ""]
    SKILLS = ["Skills", "CONTROLS"]
    INVENTORY = ["Inventory", "[D] Drop  [E] Equip  ..."]
    SPELLBOOK = ["Spellbook", ""]
    GUILD = ["Guild", ""]
    JOURNAL = ["Journal", ""]
    # ...

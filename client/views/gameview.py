import curses
import time
import os
import maps
import random
from typing import *
from .view import View, Color
from ..curses_helper import TextBox
from ..curses_helper import color_addch


class GameView(View):
    def __init__(self, game):
        super().__init__(game)

        self.game = game
        self.visible_log: Dict[float, str] = {}
        self.times_logged: int = 0

        self.win1 = None
        self.win1_height, self.win1_width = (23, 53)
        self.win1_y, self.win1_x = (3, 0)

        self.win2 = None
        self.win2_height, self.win2_width = (23, 53)
        self.win2_y, self.win2_x = (3, 53)

        self.win3 = None
        self.win3_height, self.win3_width = (13, 106)
        self.win3_y, self.win3_x = (26, 0)

        self.chatbox: Optional[TextBox] = None
        self.chatwin = None
        self.chatwin_height, self.chatwin_width = (1, self.win3_width - 8)
        self.chatwin_y, self.chatwin_x = (self.win3_y + self.win3_height, self.win3_x + 7)

        # Window 2 and focus
        self.focus: int = 1
        self.win2_focus = GameView.Window2Focus.SKILLS

    def display(self, stdscr):
        self.stdscr = stdscr
        stdscr.timeout(round(1000 / self.game.tick_rate))

        # Init windows
        self.win1 = stdscr.subwin(self.win1_height, self.win1_width, self.win1_y, self.win1_x)
        self.win2 = stdscr.subwin(self.win2_height, self.win2_width, self.win2_y, self.win2_x)
        self.win3 = stdscr.subwin(self.win3_height, self.win3_width, self.win3_y, self.win3_x)
        self.chatwin = stdscr.subwin(self.chatwin_height, self.chatwin_width, self.chatwin_y, self.chatwin_x)

        # Init chatbox
        self.chatbox = TextBox(self.chatwin, 0, 0, self.chatwin_width,
                               parentview=self, wins_to_update=(self.win1, self.win2, self.win3))

        super().display(stdscr)

    def draw(self) -> None:
        super().draw()

        # Focus control labels
        self.stdscr.hline(0, 0, curses.ACS_HLINE, self.width)

        control_title: str = ''
        control_string: str = ''
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

        # Help key
        help_string: str = "[?] Help"
        self.stdscr.addstr(1, self.width - 1 - len(help_string), help_string)

        # Adding border to windows
        self.win1.border()
        self.win2.border()
        self.win3.border()
        self.draw_chatwin_border()

        # Rendering window titles
        self.title(self.win1, "[1] Forgotten Moor", self.focus == 1)
        self.title(self.win2, f"[2] {self.win2_focus[0]}", self.focus == 2)
        self.title(self.win3, "[3] Log", self.focus == 3)

        # Window 1 content
        self.draw_map()

        # Window 2 content
        if self.win2_focus == GameView.Window2Focus.SKILLS:
            self.draw_status_win()
        elif self.win2_focus == GameView.Window2Focus.HELP:
            self.draw_help_win()

        # Window 3 content
        self.draw_log()

    def draw_map(self):
        view_radius = self.game.player.get_view_radius()
        win1_hwidth, win1_hheight = self.win1_width // 2, self.win1_height // 2
        player_pos = self.game.player.get_position()

        for row in range(-view_radius, view_radius + 1):
            for col in range(-view_radius, view_radius + 1):
                pos = (player_pos[0] + row, player_pos[1] + col)
                random.seed(hash(pos))

                if self.coordinate_exists(*pos):
                    cy, cx = win1_hheight + row, win1_hwidth + col * 2
                    for map_data in (self.game.ground_map_data, self.game.solid_map_data, self.game.roof_map_data):
                        if pos not in map_data:
                            continue
                        c = map_data[pos]
                        if c == maps.STONE:
                            color_addch(self.win1, cy, cx, '·', Color.WHITE)
                        elif c == maps.GRASS:
                            color_addch(self.win1, cy, cx, random.choice([',', '`']), Color.GREEN)
                        elif c == maps.SAND:
                            color_addch(self.win1, cy, cx, '~', Color.YELLOW)
                        elif c == maps.WATER:
                            color_addch(self.win1, cy, cx, '░', Color.BLUE)
                        elif c == maps.LEAF:
                            color_addch(self.win1, cy, cx, random.choice(['╭', '╮', '╯', '╰']), Color.GREEN)
                        elif c == maps.COBBLESTONE:
                            color_addch(self.win1, cy, cx, '░', Color.WHITE)
                        elif c == maps.WOOD:
                            color_addch(self.win1, cy, cx, '◍', Color.YELLOW)

                    # Overrides: Enter in here if solid must look different from ground, for example
                    map_data = self.game.solid_map_data
                    if pos in map_data:
                        c = map_data[pos]
                        if c == maps.STONE:
                            color_addch(self.win1, cy, cx, '█', Color.WHITE)

                    # Objects
                    if pos in self.game.visible_users.values():
                        color_addch(self.win1, cy, cx, '☺', Color.WHITE)

        # Draw player in middle of screen
        color_addch(self.win1, win1_hheight, win1_hwidth, '☺', Color.WHITE)

    def draw_help_win(self):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'assets', 'help.txt'), 'r') as helpfile:
            lines: List[str] = helpfile.readlines()
            for y, line in enumerate(lines, 2):
                self.win2.addstr(y, 2, line)

    def draw_status_win(self):
        self.win2.addstr(1, 2, f"{self.game.player.get_username()}, Guardian of Forgotten Moor")
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

    def draw_log(self):
        # Update the log if necessary
        logsize_diff: int = self.game.logger.size - self.times_logged
        if logsize_diff > 0:
            self.visible_log.update(self.game.logger.latest)
            self.times_logged += logsize_diff

            # Truncate the log to only the newest entries that will fit in the view
            log_keys = list(self.visible_log.keys())
            log_keys_to_remove = log_keys[:max(0, len(log_keys) - self.win3_height + self.chatwin_height + 2)]
            for key in log_keys_to_remove:
                del self.visible_log[key]

        if self.visible_log != {}:
            log_line: int = 2
            for utctime, message in self.visible_log.items():
                timestamp: str = time.strftime('%R', time.localtime(utctime))
                self.win3.addstr(log_line, 1, f" [{timestamp}] {message}")
                log_line += 1

        # Add chat prompt
        self.stdscr.addstr(self.chatwin_y, self.chatwin_x - 5, "Say: ")

    def draw_chatwin_border(self):
        # The chatwin is only 1 high, so the native curses border function doesn't like it.
        # Draw the border manually with stdscr.
        self.stdscr.hline(self.height - 1, 1, curses.ACS_HLINE, self.width - 2)
        self.stdscr.vline(self.chatwin_y, 0, curses.ACS_VLINE, self.chatwin_height)
        self.stdscr.vline(self.chatwin_y, self.width - 1, curses.ACS_VLINE, self.chatwin_height)
        self.stdscr.addch(self.height - 1, 0, '└')
        self.stdscr.addch(self.height - 1, self.width - 1, '┘')
        self.stdscr.vline(self.chatwin_y - 1, 0, curses.ACS_VLINE, 1)
        self.stdscr.vline(self.chatwin_y - 1, self.width - 1, curses.ACS_VLINE, 1)

    def coordinate_exists(self, y: int, x: int) -> bool:
        return 0 <= y < self.game.size[0] and 0 <= x < self.game.size[1]

    @staticmethod
    def progress_bar(value: float, max_value: float) -> str:
        percent = int(10 * (value / max_value)) + 1

        s = "[-----------]"
        s = s[:percent] + "o" + s[percent + 1:]
        return s

    @staticmethod
    def title(window, s: str, focus=False):
        if focus is False:
            window.addstr(0, 2, f"{s} ")
        else:
            window.addstr(0, 2, f"{s} ", curses.color_pair(3))

    @staticmethod
    def addstr(win, y: int, x: int, s: str, bordered=True, wrap_at_x_pos=False):
        height, width = win.getmaxyx()
        array = []

        padding = 2 if bordered else 1

        if wrap_at_x_pos:
            while x + len(s) > width - padding:
                array.append(s[:width - padding - x])
                s = s[width - padding - x:]
            array.append(s[:width - padding - x])
        else:
            if x + len(s) > width - padding:
                array.append(s[:width - padding - x])
                s = s[width - padding - x:]

            while 2 + len(s) > width - padding:
                array.append(s[:width - padding - 2])
                s = s[width - padding - 2:]

            array.append(s[:width - padding - 2])

        if y + len(array) > height - 1:
            raise Exception("String overflows window vertically.")
        else:
            if wrap_at_x_pos:
                for row in range(len(array)):
                    win.addstr(y + row, x, array[row])
            else:
                win.addstr(y, x, array[0])
                for row in range(len(array) - 1):
                    win.addstr(y + row + 1, padding, array[row + 1])

    class Window2Focus:
        HELP = ("Help", "")
        SKILLS = ("Skills", "CONTROLS")
        INVENTORY = ("Inventory", "(D) Drop  (E) Equip  ...")
        SPELLBOOK = ("Spellbook", "")
        GUILD = ("Guild", "")
        JOURNAL = ("Journal", "")
        # ...

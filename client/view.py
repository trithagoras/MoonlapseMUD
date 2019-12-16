from curses_helper import Window, Curses


class View:
    def __init__(self, stdscr: Window, curses: Curses, game):
        stdscr.keypad(1)
        stdscr.timeout(round(1000 / game.tick_rate))
        curses.curs_set(False)
        
        self.game = game

        # init window sizes
        self.height, self.width = (46, 106)

        self.win1_height, self.win1_width = (23, 53)
        self.win1_y, self.win1_x = (9, 0)
        self.win2_height, self.win2_width = (23, 53)
        self.win2_y, self.win2_x = (9, 53)
        self.win3_height, self.win3_width = (14, 106)
        self.win3_y, self.win3_x = (32, 0)

        # Init windows
        self.win1 = stdscr.subwin(self.win1_height, self.win1_width, self.win1_y, self.win1_x)
        self.win2 = stdscr.subwin(self.win2_height, self.win2_width, self.win2_y, self.win2_x)
        self.win3 = stdscr.subwin(self.win3_height, self.win3_width, self.win3_y, self.win3_x)

        # Start colors in curses
        curses.start_color()

        # init color pairs
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    def draw(self, stdscr: Window, curses: Curses):
        stdscr.erase()

        # max terminal size
        if stdscr.getmaxyx() < (46, 106):
            stdscr.addstr(0, 0, f"Must be {self.height} rows x {self.width} cols")
            stdscr.refresh()
        else:
            # Window controls labels
            stdscr.hline(0, 0, curses.ACS_HLINE, self.width)
            stdscr.addstr(0, 2, "Window Controls ")
            stdscr.addstr(1, 1, "[1/2/3] Change window focus  [ENTER] Chat")
            stdscr.addstr(3, 2, "[M] Map  [T] Travel")

            stdscr.addstr(3, self.win2_x + 2, "[I] Inventory  [P] Spellbook  [B] Equipment")
            stdscr.addstr(4, self.win2_x + 2, "[G] Guild      [K] Skills")

            # Map controls labels
            stdscr.hline(6, 0, curses.ACS_HLINE, self.width)
            stdscr.addstr(6, 2, "Map Controls ")
            stdscr.addstr(7, 1,
                          "[V] Look  [D] Pick up item  [E] Use/Equip  [←/→/↑/↓] Move  [</>] Use Stairs/Ladders")

            # Adding border to windows
            self.win1.border()
            self.win2.border()
            self.win3.border()

            # Rendering window titles
            if self.game.focus == 1:
                self.win1.addstr(0, 2, "[1] Forgotten Moor ", curses.color_pair(3))
            else:
                self.win1.addstr(0, 2, "[1] Forgotten Moor ")

            if self.game.focus == 2:
                self.win2.addstr(0, 2, "[2] Skills ", curses.color_pair(3))
            else:
                self.win2.addstr(0, 2, "[2] Skills ")

            if self.game.focus == 3:
                self.win3.addstr(0, 2, "[3] Log ", curses.color_pair(3))
            else:
                self.win3.addstr(0, 2, "[3] Log ")

            # win1 content
            for index in range(0, len(self.game.game_data['p'])):
                player = self.game.game_data['p'][index]

                if player is not None:
                    self.win1.addch(player['pos']['y'] + 1, player['pos']['x'], player['c'])

            for wall in self.game.walls:
                self.win1.addch(wall[1] + 1, wall[0], '█')

            # Window 2 content
            self.win2.addstr(1, 1, "coreyb65, Guardian of Forgotten Moor")
            self.win2.addstr(3, 1, f"Level 15 {self.progress_bar(7, 10)} (7/10 skill levels to 16)")

            self.win2.addstr(5, 1, f"Vitality      31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(6, 1, f"Strength      10/10 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(7, 1, f"Agility       31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(8, 1, f"Dexterity     31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(9, 1, f"Astrology     31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(10, 1, f"Intelligence  31/31 {self.progress_bar(3, 10)} (3,000/10,000)")

            self.win2.addstr(12, 1, f"Woodcutting   31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(13, 1, f"Crafting      31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(14, 1, f"Mining        31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(15, 1, f"Smithing      31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(16, 1, f"Fishing       31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(17, 1, f"Cooking       31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(18, 1, f"Alchemy       31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(19, 1, f"Enchanting    31/31 {self.progress_bar(3, 10)} (3,000/10,000)")
            self.win2.addstr(20, 1, f"??????????    31/31 {self.progress_bar(3, 10)} (3,000/10,000)")

            # Window 3 content
            self.win3.hline(self.win3_height - 3, 1, curses.ACS_HLINE, self.win3_width - 2)
            self.win3.addstr(self.win3_height - 2, 2, "Say: ")

            # sample lines in win3
            self.win3.addstr(3, 1, "[14:22] coreyb65 says: Hello and welcome to Moonlapse!")
            self.win3.addstr(4, 1, "[14:25] A forbidden void has opened in the Forgotten Moor!", curses.color_pair(6))

    @staticmethod
    def progress_bar(value: float, max_value: float) -> str:
        percent = int(10 * (value / max_value)) + 1

        s = "[-----------]"
        s = s[:percent] + "o" + s[percent + 1:]
        return s

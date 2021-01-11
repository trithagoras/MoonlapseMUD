import curses
import random
import time
from typing import Dict

import maps
from client.views.view import View, Window
import client.controllers.game as game


class GameView(View):
    def __init__(self, controller):
        super().__init__(controller)
        self.visible_log: Dict[float, str] = {}
        self.times_logged: int = 0

        # Init windows
        self.win1 = Window(self.controller.cs.stdscr, 3, 0, 23, 53)
        self.win2 = Window(self.controller.cs.stdscr, 3, 53, 23, 53)
        self.win3 = Window(self.controller.cs.stdscr, 26, 0, 13, 106)
        self.chatwin = Window(self.controller.cs.stdscr, self.win3.y + self.win3.height - 1, self.win3.x, 3, self.win3.width)
        self.place_widget(self.controller.chatbox, self.chatwin.y + 1, self.chatwin.x + 2)

    def draw(self):
        if not self.controller.ready():
            msg: str = "Loading, please wait..."
            self.addstr(50 // 2, (100 - len(msg)) // 2, msg)
            return

        self.win1 = Window(self.controller.cs.stdscr, 3, 0, 23, 53)
        self.win2 = Window(self.controller.cs.stdscr, 3, 53, 23, 53)
        self.win3 = Window(self.controller.cs.stdscr, 26, 0, 13, 106)
        self.chatwin = Window(self.controller.cs.stdscr, self.win3.y + self.win3.height - 1, self.win3.x, 3, self.win3.width)

        for win in [self.win1, self.win2, self.win3, self.chatwin]:
            win.border()

        # window 1 content
        self.draw_map()

        # window 2 content
        self.draw_inventory()

        # Window 3 content
        self.draw_log()

        self.addstr(2, 1, self.controller.quicklog)

    def draw_map(self):
        self.win1.title(self.controller.room.name)

        view_radius = 10
        win1_hwidth, win1_hheight = self.win1.width // 2, self.win1.height // 2
        room = self.controller.room

        for row in range(-view_radius, view_radius + 1):
            for col in range(-view_radius, view_radius + 1):
                pos = (self.controller.player_instance['y'] + row, self.controller.player_instance['x'] + col)
                random.seed(hash(pos))

                if self.coordinate_exists(*pos):
                    cy, cx = win1_hheight + row, win1_hwidth + col * 2
                    for what in ('ground', 'solid'):
                        c = room.at(what, *pos)

                        if c == maps.STONE:
                            self.win1.addstr(cy, cx, '·', 0)
                        elif c == maps.GRASS:
                            self.win1.addstr(cy, cx, random.choice([',', '`']), curses.COLOR_GREEN)
                        elif c == maps.SAND:
                            self.win1.addstr(cy, cx, '~', curses.COLOR_YELLOW)
                        elif c == maps.WATER:
                            self.win1.addstr(cy, cx, '#', curses.COLOR_BLUE)
                        elif c == maps.LEAF:
                            self.win1.addstr(cy, cx, random.choice(['╭', '╮', '╯', '╰']), curses.COLOR_GREEN)
                        elif c == maps.COBBLESTONE:
                            self.win1.addstr(cy, cx, '░', 0)
                        elif c == maps.WOOD:
                            self.win1.addstr(cy, cx, '·', curses.COLOR_YELLOW)

                    # rain splashes
                    if self.controller.weather == "Rain":
                        random.seed()
                        if room.at('ground', pos[0], pos[1]) and room.at('ceiling', pos[0], pos[1]) == maps.NOTHING:
                            if random.randrange(0, 8) == 0:
                                self.win1.addstr(cy, cx, random.choice([',', '.', '`']), curses.COLOR_BLUE)

                    # Overrides: Enter in here if solid must look different from ground, for example
                    c = room.at('solid', *pos)
                    if c == maps.STONE:
                        self.win1.addstr(cy, cx, '█', 0)
                    elif c == maps.WOOD:
                        self.win1.addstr(cy, cx, '◍', curses.COLOR_YELLOW)

        # Draw entities
        for e in self.controller.visible_instances:
            if e.id != self.controller.player_instance.id:
                y = win1_hheight + (e.y - self.controller.player_instance.y)
                x = win1_hwidth + (e.x - self.controller.player_instance.x) * 2

                typename = e.entity["typename"]

                if typename == 'Portal':
                    self.win1.addstr(y, x, 'O', curses.COLOR_CYAN)
                elif typename in ('Item', 'Pickaxe', 'Axe'):
                    self.win1.addstr(y, x, '$', curses.COLOR_MAGENTA)
                elif typename == "OreNode":
                    # different ores should mean different colors. perhaps by name?
                    self.win1.addstr(y, x, 'o', curses.COLOR_RED)
                elif typename == "TreeNode":
                    # different trees should mean different colors. perhaps by name?
                    self.win1.addstr(y, x, '♣', curses.COLOR_GREEN)
                else:
                    self.win1.addstr(y, x, '?', curses.COLOR_MAGENTA)

                # draw players above all
                if typename == 'Player':
                    self.win1.addstr(y, x, 'C', 0)

        # Draw player in middle of screen
        self.win1.addstr(win1_hheight, win1_hwidth, '@', 0)

        # if looking, draw look cursor
        if self.controller.state == game.State.LOOKING:
            cy, cx = self.controller.look_cursor_y, self.controller.look_cursor_x
            y = win1_hheight + (cy - self.controller.player_instance.y)
            x = win1_hwidth + (cx - self.controller.player_instance.x) * 2
            self.win1.addstr(y, x, 'X', 0)

    def coordinate_exists(self, y: int, x: int) -> bool:
        return 0 <= y < self.controller.room.height and 0 <= x < self.controller.room.width

    def draw_inventory(self):
        win = self.win2
        win.title("Inventory")

        win.addstr(1, 2, "Name")
        win.addstr(1, 12, "Value")
        win.addstr(1, 22, "Amount")

        line = 3
        for key, val in self.controller.inventory.items():
            name = val['item']['entity']['name']
            amount = val['amount']
            value = val['item']['value']
            win.addstr(line, 2, f"{name}")
            win.addstr(line, 12, f"{value}")
            win.addstr(line, 22, f"{amount}")
            line += 1

    def draw_log(self):
        self.win3.title("Log")

        # Update the log if necessary
        logsize_diff: int = self.controller.logger.size - self.times_logged
        if logsize_diff > 0:
            self.visible_log.update(self.controller.logger.latest)
            self.times_logged += logsize_diff

            # Truncate the log to only the newest entries that will fit in the view
            log_keys = list(self.visible_log.keys())
            log_keys_to_remove = log_keys[:max(0, len(log_keys) - self.win3.height + self.chatwin.height)]
            for key in log_keys_to_remove:
                del self.visible_log[key]

        if self.visible_log != {}:
            log_line: int = 2
            for utctime, message in self.visible_log.items():
                timestamp: str = time.strftime('%R', time.localtime(utctime))
                self.win3.addstr(log_line, 1, f" [{timestamp}] {message}")
                log_line += 1

        # Add chat prompt
        self.controller.chatbox.draw()

import curses
import randomish
import time
from typing import *

import maps
from client.views.view import View, Window
import client.controllers.game as game


class GameView(View):
    def __init__(self, controller):
        super().__init__(controller)
        self.gamelog: Dict[float, str] = {}
        self.times_logged: int = 0

        self.inventory_page = 0     # either page 0 or page 1
        self.bank_page = 0          # TODO: add more pages than 2 (extensible for any size container?)

        # Init windows
        self.win1 = Window(self.controller.cs.stdscr, 3, 0, 23, 53)
        self.win2 = Window(self.controller.cs.stdscr, 3, 53, 23, 53)
        self.win3 = Window(self.controller.cs.stdscr, 26, 0, 13, 106)
        self.focused_win = None

        self.chatwin = Window(self.controller.cs.stdscr, self.win3.y + self.win3.height - 1, self.win3.x, 3, self.win3.width)

        self.chat_scroll: int = 0   # How many lines up from the most recent logged?

        self.place_widget(self.controller.chatbox, self.chatwin.y + 1, self.chatwin.x + 2)

    def draw(self):
        if not self.controller.ready():
            msg: str = "Loading, please wait..."
            self.addstr(50 // 2, (100 - len(msg)) // 2, msg)
            return

        for win in (self.win1, self.win2, self.win3, self.chatwin):
            focused = win == self.focused_win
            win.border(color=(curses.COLOR_CYAN if focused else None))

        # window 1 content
        if self.controller.state == game.State.IN_BANK:
            self.draw_bank()
        else:
            self.draw_map()

        # window 2 content
        self.draw_inventory()

        # Window 3 content
        self.draw_log()

        self.addstr(2, 1, self.controller.quicklog)

    def draw_bank(self):
        win = self.win1
        win.title(f"[1] Bank")
        win.addstr(1, 2, "Name")
        win.addstr(1, 32, "Value")
        win.addstr(1, 42, "Amount")

        # creating list of bank items (to keep track of position)
        bank = []
        for key, val in self.controller.bank.items():
            bank.append((key, val))

        line = 3
        rng = range(15 * self.bank_page, min(15 * (self.bank_page+1), len(bank)))

        for i in rng:
            key, val = bank[i]
            name = val['item']['entity']['name']
            amount = val['amount']
            value = val['item']['value']
            win.addstr(line, 2, f"{name}")
            win.addstr(line, 32, f"{value}")
            win.addstr(line, 42, f"{amount}")
            line += 1
        
        # selected item
        win.addstr(3 + (self.controller.bank_index % 15), 1, "*")

        win.addstr(19, 2, "↑ or ↓ to choose item")      # todo: change keybind and implement this
        win.addstr(20, 2, f"← or → to flip page (current page {self.bank_page+1})")
        win.addstr(21, 2, "[w]ithdraw single or [W]ithdraw all")

    def draw_map(self):
        self.win1.title(f"[1] {self.controller.room.name}")

        view_radius = 10
        win1_hwidth, win1_hheight = self.win1.width // 2, self.win1.height // 2
        room = self.controller.room

        for row in range(-view_radius, view_radius + 1):
            for col in range(-view_radius, view_radius + 1):
                pos = (self.controller.player_instance['y'] + row, self.controller.player_instance['x'] + col)
                randomish.seed(randomish.fast_hash(*pos))

                if self.controller.room.coordinate_exists(*pos):
                    cy, cx = win1_hheight + row, win1_hwidth + col * 2
                    for what in ('ground', 'solid'):
                        c = room.at(what, *pos)

                        if c == maps.STONE:
                            self.win1.addstr(cy, cx, '·', 0)
                        elif c == maps.GRASS:
                            self.win1.addstr(cy, cx, randomish.choice([',', '`']), curses.COLOR_GREEN)
                        elif c == maps.SAND:
                            self.win1.addstr(cy, cx, '~', curses.COLOR_YELLOW)
                        elif c == maps.WATER:
                            self.win1.addstr(cy, cx, '#', curses.COLOR_BLUE)
                        elif c == maps.LEAF:
                            self.win1.addstr(cy, cx, randomish.choice(['╭', '╮', '╯', '╰']), curses.COLOR_GREEN)
                        elif c == maps.COBBLESTONE:
                            self.win1.addstr(cy, cx, '░', 0)
                        elif c == maps.WOOD:
                            self.win1.addstr(cy, cx, '·', curses.COLOR_YELLOW)

                    # rain splashes
                    if self.controller.weather == "Rain":
                        randomish.seed()
                        if room.at('ground', pos[0], pos[1]) and room.at('ceiling', pos[0], pos[1]) == maps.NOTHING:
                            if randomish.randrange(0, 8) == 0:
                                self.win1.addstr(cy, cx, randomish.choice([',', '.', '`']), curses.COLOR_BLUE)

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
                elif typename in ('Item', 'Pickaxe', 'Axe', 'Ore', 'Logs'):
                    self.win1.addstr(y, x, '$', curses.COLOR_MAGENTA)
                elif typename == "OreNode":
                    # different ores should mean different colors. perhaps by name?
                    self.win1.addstr(y, x, 'o', curses.COLOR_RED)
                elif typename == "TreeNode":
                    # different trees should mean different colors. perhaps by name?
                    self.win1.addstr(y, x, '♣', curses.COLOR_GREEN)
                elif typename == 'Bank':
                    self.win1.addstr(y, x, '$', curses.COLOR_YELLOW)
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

    def draw_inventory(self):
        win = self.win2
        win.title("[2] Inventory")

        win.addstr(1, 2, "Name")
        win.addstr(1, 32, "Value")
        win.addstr(1, 42, "Amount")

        # creating list of inventory items (to keep track of position)
        inv = []
        for key, val in self.controller.inventory.items():
            inv.append((key, val))

        line = 3
        if self.inventory_page == 0:
            rng = range(0, min(15, len(inv)))
        else:
            rng = range(15, min(30, len(inv)))

        for i in rng:
            key, val = inv[i]
            name = val['item']['entity']['name']
            amount = val['amount']
            value = val['item']['value']
            win.addstr(line, 2, f"{name}")
            win.addstr(line, 32, f"{value}")
            win.addstr(line, 42, f"{amount}")
            line += 1

        # selected item
        win.addstr(3 + (self.controller.inventory_index % 15), 1, "*")

        win.addstr(19, 2, "[ or ] to choose item")      # todo: change keybind and implement this
        win.addstr(20, 2, f"[<] or [>] to flip page (current page {self.inventory_page+1})")
        if self.controller.state == game.State.IN_BANK:
            win.addstr(21, 2, "[d]eposit single or [D]eposit all")
        else:
            win.addstr(21, 2, "[d]rop single or [D]rop all")

    def draw_log(self):
        title = "[3] Log"
        if self.chat_scroll > 0:
            title += f" ({self.chat_scroll} more ↓)"
        self.win3.title(title)

        # Update the log if necessary
        logsize_diff: int = self.controller.logger.size - self.times_logged
        if logsize_diff > 0:
            self.gamelog.update(self.controller.logger.latest)
            self.times_logged += logsize_diff

        if self.gamelog != {}:
            log_line: int = 2
            gamelog_ordered: List[Tuple[float, str]] = list(self.gamelog.items())

            if self.times_logged >= self.win3.height - self.chatwin.height:
                # There is overflow to worry about so we need to truncate
                gamelog_start_idx = (self.times_logged - self.win3.height + self.chatwin.height) - self.chat_scroll
                gamelog_end_idx = gamelog_start_idx + self.win3.height - self.chatwin.height
                gamelog_ordered = gamelog_ordered[gamelog_start_idx: gamelog_end_idx]

            for idx, (utctime, message) in enumerate(gamelog_ordered):
                timestamp: str = time.strftime('%R', time.localtime(utctime))
                self.win3.addstr(idx + 2, 1, f" [{timestamp}] {message}")

        # Add chat prompt
        self.controller.chatbox.draw()

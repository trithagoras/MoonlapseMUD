import time

import rsa

from networking import packet


class Controller:
    def __init__(self, cs):
        self.cs = cs
        self.view = None
        self.running = False

        self.widgets = []

    def start(self):
        self.running = True
        self.view.start()

        # begin main loop
        while self.running:
            self._process_packet()
            self.update()
            self.view._draw()
            self.cs.stdscr.refresh()
            self._get_input()

    def ready(self):
        pass

    def update(self):
        pass

    def _process_packet(self):
        if not self.cs.packets:
            return

        p = self.cs.packets.pop(0)
        if not self.process_packet(p):
            self.cs.packets.insert(0, p)

    def process_packet(self, p) -> bool:
        pass

    def _get_input(self):
        key = self.cs.stdscr.getch()
        self.process_input(key)

    def process_input(self, key: int):
        pass

    def process_exit(self):
        pass

    def stop(self):
        self.running = False
        self.view.stop()


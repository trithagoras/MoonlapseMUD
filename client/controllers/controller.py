import curses
import time

class Debug:
    def __init__(self, controller):
        self.controller = controller
        self.show = False

        # FPS stuff
        self._fps = 0
        self._frames = 0
        self._frame_start_time = time.time()

    def update_fps(self):
        """Call this inside the main game loop for it to work correctly"""
        now = time.time()
        if now - self._frame_start_time >= 1:
            self._fps = self._frames
            self._frames = 0
            self._frame_start_time = now
        self._frames += 1

    def draw(self):
        if self.show:
            self.controller.cs.stdscr.addstr(0, 0, f"FPS: {self._fps}")


class Controller:
    def __init__(self, cs):
        self.cs = cs
        self.view = None
        self.debug = Debug(self)
        self.running = False
        self._target_fps = 60

        self.widgets = []


    def start(self):
        self.running = True
        self.view.start()


        # begin main loop
        while self.running:
            now = time.time()
            self.debug.update_fps()

            # Process the frame
            self._get_input()
            self._process_packet()
            self.update()
            self.view._draw()
            self.cs.stdscr.refresh()

            # Calculate if we're under or over time budget and sleep accordingly
            delta_t = time.time() - now
            naptime = 1 / self._target_fps - delta_t
            if naptime > 0:
                curses.napms(round(naptime * 1000))
            else:
                # We're experiencing lag
                # TODO: Do something... lol
                pass

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
        if key == curses.KEY_F12:
            # Toggle debug mode
            self.debug.show = not self.debug.show

    def process_exit(self):
        pass

    def stop(self):
        self.running = False
        self.view.stop()


import curses
import curses.ascii
import os
from client.views.view import View


class Controller:
    def __init__(self):
        self.view: View = View(self)

    def start(self) -> None:
        """
        Gets this controller to start the view and loop handling input. Can be called any time you need to bring
        this controller / view into action after it's been initialised.
        """

        # Eliminate delay in the program after the ESC key is pressed
        os.environ.setdefault('ESCDELAY', '25')

        # Start the view
        curses.wrapper(self.view.display)

    def stop(self) -> None:
        """
        Stops this controller. By default, this involves stopping the view associated with this controller. When
        implementing this method, call super().stop() last.
        """
        self.view.stop()

    def handle_input(self) -> int:
        """
        Gets input from the view's main loop (kinda gross but oh well) and returns the next keycode pressed.
        """
        return self.view.stdscr.getch()

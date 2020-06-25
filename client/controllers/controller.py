import curses
import curses.ascii
import json
import socket as sock
import sys
import os
import time
import traceback
from threading import Thread
from typing import *

from client.views import View


class Controller:
    def __init__(self):
        self.view: View = View(self)

    def start(self):
        # Eliminates an annoying delay in the program after the ESC key is pressed
        os.environ.setdefault('ESCDELAY', '25')

        # Start the view
        curses.wrapper(self.view.display)

    def stop(self) -> None:
        pass

    def get_input(self) -> None:
        pass

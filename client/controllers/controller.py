import curses
import curses.ascii
import json
import socket as sock
import sys
import time
import traceback
from threading import Thread
from typing import *

from client.views import View


class Controller:
    def __init__(self):
        self.view: View = View(self)

    def start(self):
        curses.wrapper(self.view.display)

    def get_input(self) -> None:
        pass

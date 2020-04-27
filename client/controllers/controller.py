import socket as sock
import json
import sys
from threading import Thread
import curses
from typing import *
import curses.ascii
import traceback
import time

from ..views import *


class Controller:
    def __init__(self):
        self.view: View = View(self)

    def start(self):
        curses.wrapper(self.view.display)

    def get_input(self) -> None:
        pass







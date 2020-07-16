import time
import os
from typing import *


class Log:
    def __init__(self):
        self.latest: Dict[float, str] = {}
        self.size: int = 0

    def log(self, message: str):
        # Log times as seconds since 1-Jan-1970 (Unix time)
        timestamp: float = time.time()

        self.latest = {timestamp: message}
        self.size += 1

        logdir: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs')
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        datestr: str = time.strftime('%Y-%m-%d', time.gmtime())
        logfile: str = os.path.join(logdir, f"{datestr}.log")
        with open(logfile, 'a') as f:
            print(f"{time.strftime('%R', time.gmtime(timestamp))}: {message}", file=f)

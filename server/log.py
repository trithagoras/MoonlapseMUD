import time
import os


class Log:
    def __init__(self):
        self.state = {
            'log': {}
        }
        self.latest = None

    def log(self, timestamp: float, message: str):
        # Log times as seconds since 1-Jan-1970 (Unix time)
        self.latest = {timestamp: message}
        self.state['log'].update(self.latest)

        logdir: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs')
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        datestr: str = time.strftime('%Y-%m-%d', time.gmtime())
        logfile: str = os.path.join(logdir, f"{datestr}.log")
        with open(logfile, 'a') as f:
            print(f"{time.strftime('%R', time.gmtime(timestamp))}: {message}", file=f)

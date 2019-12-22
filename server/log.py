import time


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

        datestr: str = time.strftime('%Y-%m-%d', time.gmtime())
        with open(f"{datestr}.log", 'a') as f:
            print(f"{time.strftime('%R', time.gmtime(timestamp))}: {message}", file=f)

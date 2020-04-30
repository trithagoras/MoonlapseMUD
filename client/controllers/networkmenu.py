import socket as sock
import sys
import traceback

from .menu import Menu


class NetworkMenu(Menu):
    """
    A menu which requires a connection to the server to send and receive
    packets. Examples include a login menu or a registration menu.
    """
    def __init__(self, host: str, port: int, menu: dict):
        super().__init__(menu)

        self.addr = (host, port)
        self.s: sock.socket = None

    """
    Attempts to connect to the network and start the menu. Returns an error
    message if unsuccessful.
    """
    def start(self, attempt=0) -> str:
        max_attempts: int = 3
        self.s: sock.socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        try:
            self.s.connect(self.addr)
        except sock.error as e:
            if attempt < max_attempts:
                # Socket might have closed, open it again
                self.start(attempt=attempt+1)
                print(traceback.format_exc(), file=sys.stderr)
            else:
                # Something else is wrong, exit
                print(f"Error: Connection attempts reached max ({max_attempts}). Trackback: ", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                self.view.stop()
                return str(e)

        super().start()

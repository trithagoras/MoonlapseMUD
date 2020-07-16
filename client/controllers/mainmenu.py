import socket
from networking import packet
from .loginmenu import LoginMenu
from .menu import Menu
from .registermenu import RegisterMenu
from ..views.menuview import MenuView


class MainMenu(Menu):
    def __init__(self, s: socket.socket):
        super().__init__({
            "Login": self.login,
            "Register": self.register
        })

        self.s: socket.socket = s

        self.view = MenuView(self, "Welcome to MoonlapseMUD")

        # Receive the message of the day
        p: packet.Packet = packet.receive(self.s)
        if isinstance(p, packet.WelcomePacket):
            self.view.title = p.payloads[0].value

    def login(self):
        LoginMenu(self.s).start()
        self.start()

    def register(self):
        RegisterMenu(self.s).start()
        self.start()

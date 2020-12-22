import socket
from networking import packet
from .loginmenu import LoginMenu
from .menu import Menu
from .registermenu import RegisterMenu
from ..views.menuview import MenuView
import rsa


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
        # if isinstance(p, packet.WelcomePacket):
        #     self.view.title = p.payloads[0].value
        if isinstance(p, packet.ClientKeyPacket):
            self.public_key = rsa.PublicKey(p.payloads[0].value, p.payloads[1].value)

    def login(self):
        LoginMenu(self.s, self.public_key).start()
        self.start()

    def register(self):
        RegisterMenu(self.s, self.public_key).start()
        self.start()

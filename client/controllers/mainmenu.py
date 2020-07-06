from ..views.loginview import LoginView
from ..views.menuview import MenuView
from ..views.registerview import RegisterView
from .loginmenu import LoginMenu
from .menu import Menu
from .registermenu import RegisterMenu
from networking import packet
import socket

class MainMenu(Menu):
    def __init__(self, s: socket.socket):
        super().__init__({
            "Login": self.login,
            "Register": self.register
        })

        self.s: socket.socket = s

        self.view = MenuView(self, f"Welcome to MoonlapseMUD")

        p: packet.Packet = packet.receive(self.s)
        if isinstance(p, packet.WelcomePacket):
            motd: str = p.payloads[0].value
        self.view.title = motd

    def login(self):
        loginmenu = LoginMenu(self.s)
        loginmenu.start()
        self.start()

    def register(self):
        registermenu = RegisterMenu(self.s)
        registermenu.start()
        self.start()

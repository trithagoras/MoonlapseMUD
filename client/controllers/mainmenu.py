from client.utils import NetworkState
from networking import packet
from .loginmenu import LoginMenu
from .menu import Menu
from .registermenu import RegisterMenu
from ..views.menuview import MenuView
import rsa


class MainMenu(Menu):
    def __init__(self, ns: NetworkState):
        super().__init__({
            "Login": self.login,
            "Register": self.register
        })

        self.ns = ns
        self.view = MenuView(self, "Welcome to MoonlapseMUD")

        # Receive the message of the day
        # if isinstance(p, packet.WelcomePacket):
        #     self.view.title = p.payloads[0].value

        # receive public key
        p = self.ns.receive_packet()
        if isinstance(p, packet.ClientKeyPacket):
            self.ns.public_key = rsa.PublicKey(p.payloads[0].value, p.payloads[1].value)

    def login(self):
        LoginMenu(self.ns).start()
        self.start()

    def register(self):
        RegisterMenu(self.ns).start()
        self.start()

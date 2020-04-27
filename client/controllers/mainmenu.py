from .menu import Menu
from .loginmenu import LoginMenu
from .registermenu import RegisterMenu
from ..views.menuview import MenuView
from ..views.loginview import LoginView
from ..views.registerview import RegisterView


class MainMenu(Menu):
    def __init__(self, host, port):
        super().__init__({
            "Login": self.login,
            "Register": self.register
        })

        self.host = host
        self.port = port

        self.view = MenuView(self, f"Welcome to {host}:{port}")

    def login(self):
        loginmenu = LoginMenu(self.host, self.port)
        err: str = loginmenu.start()
        if err:
            self.view.title = err
            return
        self.start()

    def register(self):
        registermenu = RegisterMenu(self.host, self.port)
        err: str = registermenu.start()
        if err:
            self.view.title = err
            return
        self.start()

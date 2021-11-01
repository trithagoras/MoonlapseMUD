import curses
import curses.ascii
import os
import pathlib
import configparser
from . import keybindings

import rsa

from client import config
from client.controllers.controller import Controller
from client.controllers.widgets import Button, CheckBox, TextField
from client.views.menuviews import MainMenuView, LoginView, RegisterView
from networking import packet


class Menu(Controller):
    def __init__(self, cs):
        super().__init__(cs)
        self.cursor = 0

    def process_input(self, key: int):
        super().process_input(key)
        for widget in self.widgets:
            if widget.selected:
                widget.process_input(key)
                return

        # menu controls
        if key == curses.KEY_UP:
            self.cursor = max(0, self.cursor - 1)
        elif key == curses.KEY_DOWN:
            self.cursor = min(len(self.widgets) - 1, self.cursor + 1)
        elif key == curses.ascii.TAB:
            self.cursor = (self.cursor + 1) % len(self.widgets)
        elif keybindings.enter(key):
            self.widgets[self.cursor].select()
        elif curses.ascii.isprint(key):
            if isinstance(self.widgets[self.cursor], TextField):
                field = self.widgets[self.cursor]
                field.value = chr(key)
                field.cursor = 1
                field.select()
        elif key == curses.ascii.ESC:
            self.process_exit()

    def process_packet(self, p) -> bool:
        if isinstance(p, packet.DenyPacket):
            self.view.title = p.payloads[0].value
        elif isinstance(p, packet.ServerTickRatePacket):
            self.cs.ns.tickrate = p.payloads[0].value
        else:
            return False

        return True


class MainMenu(Menu):
    def __init__(self, cs):
        super().__init__(cs)
        self.view = MainMenuView(self)

        self.widgets.append(Button(self, "Login", self.cs.change_controller, "LoginMenu"))
        self.widgets.append(Button(self, "Register", self.cs.change_controller, "RegisterMenu"))

        self.view.place_widget(self.widgets[0], 10, 10)
        self.view.place_widget(self.widgets[1], 14, 10)

    def process_exit(self):
        self.stop()
        self.cs.running = False

    def process_packet(self, p) -> bool:
        if super().process_packet(p):
            return True
        elif isinstance(p, packet.ClientKeyPacket):
            self.cs.ns.server_public_key = rsa.PublicKey(p.payloads[0].value, p.payloads[1].value)
        elif isinstance(p, packet.OkPacket):
            pass
        elif isinstance(p, packet.WelcomePacket):
            self.view.title = p.payloads[0].value
            pass
        else:
            return False

        return True


class LoginMenu(Menu):
    def __init__(self, cs):
        super().__init__(cs)
        self.view = LoginView(self)

        self.widgets.append(TextField(self, title="Username: ", max_length=30))
        self.widgets.append(TextField(self, title="Password: ", censored=True, max_length=200))
        self.widgets.append(CheckBox(self, text="Remember username?"))
        self.widgets.append(Button(self, "Login", self.login))

        self.view.place_widget(self.widgets[0], 10, 10)

        # Fill saved username and remember preference
        self.widgets[0].value = config.get_config_option(config.SAVED_USERNAME)
        if self.widgets[0].value:
            self.widgets[2].checked = True

        self.view.place_widget(self.widgets[1], 14, 10)
        self.view.place_widget(self.widgets[2], 18, 10)
        self.view.place_widget(self.widgets[3], 22, 10)

    def login(self):
        username = self.widgets[0].value
        password = self.widgets[1].value

        if "" in (username, password):
            self.view.title = "Username or password must not be blank"
            return

        # Remember or forget username
        if self.widgets[2].checked:
            config.set_config_option(config.SAVED_USERNAME, username)
        else:
            config.remove_config_option(config.SAVED_USERNAME)

        self.cs.ns.send_packet(packet.LoginPacket(username, password))

    def process_exit(self):
        self.cs.change_controller("MainMenu")

    def process_packet(self, p) -> bool:
        if super().process_packet(p):
            return True
        elif isinstance(p, packet.OkPacket):
            self.cs.ns.username = self.widgets[0].value
            self.cs.change_controller("Game")
        else:
            return False

        return True


class RegisterMenu(Menu):
    def __init__(self, cs):
        super().__init__(cs)
        self.view = RegisterView(self)

        self.widgets.append(TextField(self, title="Username: ", max_length=30))
        self.widgets.append(TextField(self, title="Password: ", censored=True, max_length=200))
        self.widgets.append(TextField(self, title="Confirm Password: ", censored=True, max_length=200))
        self.widgets.append(Button(self, "Register", self.register))

        self.view.place_widget(self.widgets[0], 10, 10)
        self.view.place_widget(self.widgets[1], 14, 10)
        self.view.place_widget(self.widgets[2], 18, 10)
        self.view.place_widget(self.widgets[3], 22, 10)

    def register(self):
        username = self.widgets[0].value
        password = self.widgets[1].value
        confirmpword = self.widgets[2].value

        if "" in (username, password):
            self.view.title = "Username or password must not be blank"
            return

        if password != confirmpword:
            self.view.title = "Password does not match confirmed password"
            return

        self.cs.ns.send_packet(packet.RegisterPacket(username, password))

    def process_exit(self):
        self.cs.change_controller("MainMenu")

    def process_packet(self, p) -> bool:
        if super().process_packet(p):
            return True
        elif isinstance(p, packet.OkPacket):
            self.view.title = "Registration successful! Press Esc to return to main menu"
        else:
            return False

        return True

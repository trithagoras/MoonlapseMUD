import curses
import json
import os
import random
import string
import threading
import time
from typing import *
import math

from networking import cryptography
import rsa

from client.controllers.game import Game
from client.controllers import menus
from client.views.view import Window
from networking import packet


class NetworkState:
    """
    Higher level abstraction for keeping network state. Keeps public_key and socket in neat spot.
    """

    def __init__(self, socket):
        self.socket = socket
        self.server_public_key = None
        self.aes_key: bytes = os.urandom(32)
        self.username = ""
        self.tickrate = 20

    def send_packet(self, p: packet.Packet):
        """
        Converts packet to bytes; then encrypts bytes; then converts to netstring; then send over socket
        :param p: packet to send
        """
        self._send(p, self.socket)

    def receive_packet(self) -> packet.Packet:
        return self._receive(self.socket)

    def _to_netstring(self, data: bytes) -> bytes:
        length = len(data)
        return str(length).encode('ascii') + b':' + data + b','

    def _send(self, p: packet.Packet, s) -> bytes:
        """
        Converts a Packet to bytes and sends it over a socket. Ensures all the data is sent and no more.
        """
        b = p.tobytes()
        if isinstance(p, packet.ClientKeyPacket):  # Must encrypt our key with the server's public key
            b = cryptography.encrypt_rsa(b, self.server_public_key)
        else:  # Everything else we encrypt with AES
            b = cryptography.encrypt_aes(b, self.aes_key)
        b = self._to_netstring(b)

        failure = s.sendall(b)
        if failure is not None:
            self._send(p, s)
        return b

    def _receive(self, s) -> packet.Packet:
        """
        Receives a netstring bytes over a socket. Ensure all data is received and no more. Then
        converts the data into the original Packet (preserving the exact type from the ones defined
        in this module) and original payloads depickled as python objects.

        Arguments:
            s {socket.socket} -- The socket to receive netstring-encoded packets over.

        Raises:
            PacketParseError: If the netstring is too long or there was an error reading the length of the
                              netstring.

        Returns:
            Packet -- The original Packet that was sent with the exact subtype preserved. All original
                      payloads associated are depickled as python objects.
        """
        length: bytes = b''
        while len(length) <= len(str(packet.Packet.MAX_LENGTH)):
            c: bytes = s.recv(1)
            if c != b':':
                try:
                    int(c)
                except ValueError:
                    raise PacketParseError(
                        f"Error reading packet length. So far got {length} but next digit came in as {c}.")
                else:
                    length += c
            else:
                if len(length) < 1:
                    raise PacketParseError(f"Parsing packet but length doesn't seem to be a number. Got {length}.")
                data: bytes = s.recv(int(length))

                # Perhaps all the data is not received yet
                while len(data) < int(length):
                    nextLength = int(length) - len(data)
                    data += s.recv(nextLength)

                # Read off the trailing comma
                s.recv(1)

                try:
                    # If the data is AES encrypted, decrypt with AES
                    data = cryptography.decrypt_aes(data, self.aes_key)
                    return packet.frombytes(data)
                except Exception:
                    # If the packet came through unencrypted it must be the server's public key
                    server_key_packet = packet.frombytes(data)
                    server_key_n = server_key_packet.payloads[0].value
                    server_key_e = server_key_packet.payloads[1].value
                    self.server_public_key = cryptography.load_rsa_key_from_parts(server_key_n, server_key_e)

                    # Now we have the server's public key, use it to send off our private AES key
                    client_key_packet = packet.ClientKeyPacket(self.aes_key.decode('latin1'))
                    self.send_packet(client_key_packet)
                    return packet.OkPacket()

        raise PacketParseError("Error reading packet length. Too long.")


class PacketParseError(Exception):
    pass


class ClientState:
    def __init__(self, stdscr, ns: NetworkState):
        self.ns = ns
        self.controller = None
        self.stdscr = stdscr
        self.running = True

        win_height, win_width = 40, 106
        term_height, term_width = stdscr.getmaxyx()
        if (term_height, term_width) < (win_height, win_width):
            raise curses.error(f"Screen dimensions must be {win_height} rows x {win_width} cols (detected {term_height} x {term_width})")
        self.window = Window(self.stdscr, 0, 0, win_height, win_width)

        self.packets = []

        # Listen for data in its own thread
        threading.Thread(target=self._receive_data, daemon=True).start()

        self.init_curses()
        self.change_controller("MainMenu")

    def init_curses(self):
        self.stdscr.keypad(True)
        self.stdscr.nodelay(True)

        # Start colors in curses
        curses.start_color()

        # Init color pairs
        curses.init_pair(curses.COLOR_WHITE, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(curses.COLOR_CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)

        curses.curs_set(False)

    def change_controller(self, controller: str):
        if self.controller:
            self.controller.stop()
        if controller == Game.__name__:
            self.controller = Game(self)
        elif controller == menus.MainMenu.__name__:
            self.controller = menus.MainMenu(self)
        elif controller == menus.LoginMenu.__name__:
            self.controller = menus.LoginMenu(self)
        elif controller == menus.RegisterMenu.__name__:
            self.controller = menus.RegisterMenu(self)

        self.controller.start()

    def _receive_data(self):
        while self.running:
            try:
                p = self.ns.receive_packet()
                self.packets.append(p)
            except Exception as e:
                pass


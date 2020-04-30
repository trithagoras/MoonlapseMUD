import socket
import json
import sys
import time
import os
from typing import *
from room import Room, RoomFullException
from log import Log
from threading import Thread
from threading import Timer
import traceback
from twisted.internet import task
from twisted.internet import reactor

from database import Database

from networking import models
from networking import packet as pack

import select

class TcpServer:
    def __init__(self, ip: str, port: int, database: Database):
        self.ip: str = ip
        self.port: int = port
        self.sock: socket.socket = None
        self.database: Database = database

        self.sockets: List[socket.socket] = []

        self.log: Log = Log()
        self.tick_rate: int = 100

        pwd: str = os.path.dirname(__file__)
        room_data_filename: str = os.path.join(pwd, '..', 'maps', 'map.bmp.json')
        room_data: Optional[str] = None
        with open(room_data_filename, 'r') as room_data_file:
            room_data = json.load(room_data_file)
        self.rooms: List[Optional[Room]] = [
            Room(self, room_data, 10)
        ]

    def start(self) -> None:
        """
        Start the server by configuring the socket and binding to the 
        IP / port. Also establishes connection to the database and begins 
        listening to incoming client connections and updating these clients 
        from the room they are in.
        """
        self._connect_socket()
        self.database.connect()

        # Listen to incoming client connections on its own thread
        Thread(target=self._accept_clients, daemon=True).start()

        # Update each room's players' clients exactly on every server tick
        for room in self.rooms:
            update_tick_loop = task.LoopingCall(room.update_clients)
            update_tick_loop.start(1 / self.tick_rate)
            reactor.run()

    def _connect_socket(self) -> None:
        print("Connecting to socket... ", end='')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind((self.ip, self.port))
        self.sock.listen(16)
        self.sockets.append(self.sock)
        print(f"Done.")

    def _accept_clients(self) -> None:
        while self.sockets:
            print("Waiting for a socket ready to read...")
            read_sockets, _, except_sockets = select.select(self.sockets, [], self.sockets)

            for s in read_sockets:
                print("A socket is ready!")
                if s == self.sock:
                    client_sock, client_addr = self.sock.accept()
                    client_sock.setblocking(False)
                    print("Accepted a new client!")
                    self.sockets.append(client_sock)
                else:
                    self._handle_client(s)

            for s in except_sockets:
                self.sockets.remove(s)
                s.close()

    def _handle_client(self, client_socket: socket.socket):
        packet: pack.Packet = pack.receivepacket(client_socket)

        print(f"Received data from a client: {packet}")

        if isinstance(packet, pack.LoginPacket):
            username: str = packet.payloads[0].value
            password: str = packet.payloads[1].value
            print(f"Attempting login of username {username} and password {password}")

            if self.database.user_exists(username):
                print(f"Username match found...", end='')
                if self.database.password_correct(username, password):
                    print("Password also matched!")

                    # TODO: Allow player to spawn in their last known room
                    # Try to spawn the player into the next available room
                    for room in self.rooms:
                        try:
                            Thread(target=room.spawn(client_socket, username), daemon=True).start()
                            print("Spawned player")
                        except RoomFullException:
                            client_socket.close()
                            continue
                else:
                    print("Incorrect password.")
                    client_socket.close()
            else:
                print("No username match in database.")
                client_socket.close()

        elif isinstance(packet, pack.RegisterPacket):
            username = packet.payloads[0].value
            password = packet.payloads[1].value
            print(f"Attempting registration of username {username} and password {password}")

            if self.database.user_exists(username):
                print(f"User already exists.")
                client_socket.close()
            else:
                print(f"Registration successful!")
                self.database.register_player(username, password)

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

from networking import models
from networking import packet as pack

class TcpServer:
    def __init__(self, ip, port, database):
        self.ip = ip
        self.port = port
        self.sock = None
        self.database = database

        self.log: Log = Log()
        self.tick_rate = 100

        pwd: str = os.path.dirname(__file__)
        room_data_filename: str = os.path.join(pwd, '..', 'maps', 'map.bmp.json')
        room_data: Optional[str] = None
        with open(room_data_filename, 'r') as room_data_file:
            room_data = json.load(room_data_file)
        self.rooms: List[Optional[Room]] = [
            Room(self, room_data, 10)
        ]

    def start(self):
        self.connect_socket()
        self.connect_database()

        # Start threads
        accept_thread: Thread = Thread(target=self.accept_clients)
        accept_thread.start()
        update_thread: Thread = Thread(target=self.update_clients)
        update_thread.start()

        time.sleep(0.0001)

        # Wait for threads to finish
        accept_thread.join()
        update_thread.join()

    def connect_socket(self):
        print("Connecting to socket... ", end='')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.ip, self.port))
        self.sock.listen(16)

        print(f"done: {self.sock.getsockname()}")

    def connect_database(self):
        try:
            self.database.connect()
        except Exception:
            print("Error: Traceback: ", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)

    def accept_clients(self) -> None:
        while True:
            # Establish connecting to the new client
            print("Waiting to receive data from any client...")

            try:
                client_socket, address = self.sock.accept()
            except Exception:
                print(f"Error while accepting new client... Trying again. Traceback: ", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                self.connect_socket()
                time.sleep(1)
                continue

            # Check for login and register packets from the new client
            packet: pack.Packet = pack.receivepacket(client_socket)

            try:
                print(f"Received data from client {client_socket}: {packet}")

                if isinstance(packet, pack.LoginPacket):
                    print("PAYLOAD="+str(packet.payloads[0]))
                    print("VALUE="+packet.payloads[0].value)
                    username: str = packet.payloads[0].value
                    password: str = packet.payloads[1].value
                    print(f"Got username: {username} and password: {password}")

                    if self.database.user_exists(username):
                        print(f"Incoming login request from {username}...", end='')
                        if self.database.password_correct(username, password):
                            print("Password matched!")

                            # TODO: Allow player to spawn in their last known room
                            # Try to spawn the player into the next available room
                            for room in self.rooms:
                                try:
                                    room.spawn(client_socket, username)
                                except RoomFullException:
                                    client_socket.close()
                                    continue
                        else:
                            print("Incorrect password.")
                    else:
                        print("No username match in database.")
                        client_socket.close()

                elif isinstance(packet, pack.RegisterPacket):
                    username = packet.payloads[0].value
                    password = packet.payloads[1].value
                    print(f"Got username: {username} and password: {password}")

                    if self.database.user_exists(username):
                        print(f"Attempted registration for {username} but user already exists.", end='')
                        client_socket.close()
                    else:
                        print(f"Attempted registration for {username}, continuing...")
                        self.database.register_player(username, password)
                        client_socket.close()

            except Exception:
                print("Error: Traceback: ", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                continue
        print("Oops... No longer listening to client data...", file=sys.stderr)


    def update_clients(self) -> None:
        while True:
            try:
                for room in self.rooms:
                    room.update_clients()
                time.sleep(1 / self.tick_rate)

            except KeyboardInterrupt:
                for room in self.rooms:
                    for s in room.player_sockets.values():
                        s.disconnect()
                    self.sock.close()
                    exit()

            except Exception:
                print("Error: Traceback: ", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)

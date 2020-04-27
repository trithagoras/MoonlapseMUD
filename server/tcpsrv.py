import socket
import json
import sys
import time
import os
from typing import *
from room import Room
from player import Player
from log import Log
from threading import Thread
import traceback


class TcpServer:
    def __init__(self, ip, port, database):
        self.ip = ip
        self.port = port
        self.sock = None
        self.database = database

        self.log: Log = Log()
        self.tick_rate = 100

        pwd: str = os.path.dirname(__file__)
        self.rooms: List[Optional[Room]] = [
            Room(self, os.path.join(pwd, '..', 'maps', 'map.bmp.json'), 10)
        ]

    def start(self):
        self.connect_database()

        Thread(target=self.accept_clients, daemon=True).start()
        while True:
            try:
                self.update_clients()
                time.sleep(1 / self.tick_rate)

            except KeyboardInterrupt:
                for room in self.rooms:
                    for player in room.players:
                        if player is not None:
                            player.disconnect()
                    self.sock.close()
                    exit()

            except Exception:
                print("Error: Traceback: ", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                pass

    def connect_socket(self):
        print("Connecting to socket... ", end='')
        if self.sock:
            self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
            try:
                client_socket, address = self.sock.accept()
            except socket.error as e:
                print(f"Socket error while accepting new client ({e})... Trying again. Traceback: ", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                self.connect_socket()
                time.sleep(1)
                continue
            except Exception:
                print("Error: Traceback: ", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                continue

            # Check for login and register packets from the new client
            data = ''
            try:
                while True:
                    data += client_socket.recv(1024).decode('utf-8')

                    if data[-1] == ';':
                        break

            except IndexError:
                print("Error: No data. Traceback: ", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                client_socket.close()
                continue

            try:
                data = json.loads(data[:-1])
                action: str = data['a']
                payload: str = data['p']
                try:
                    payload2 = data['p2']
                except KeyError:
                    print(f"Error: KeyError finding key 'p2' in dictionary {data}. Traceback: ", file=sys.stderr)
                    print(traceback.format_exc())
                    payload2 = ''

                print(f"Received data from client {client_socket}: Action={action}, Payload={payload}:{payload2}")

                if action == 'login':
                    username = payload
                    password = payload2
                    print(f"Got username: {username.replace(' ', '_')} and password: {password.replace(' ', '_')}")

                    if self.database.user_exists(username):
                        print(f"Incoming login request from {username}...", end='')
                        if self.database.password_correct(username, password):
                            print("Password matched!")

                            player: Player = Player(client_socket, username)

                            # TODO: Allow player to spawn in their last known room
                            # Try to spawn the player into the next available room
                            for room in self.rooms:
                                try:
                                    room.spawn(player)
                                except Exception:
                                    print("Error: Traceback: ", file=sys.stderr)
                                    print(traceback.format_exc(), file=sys.stderr)
                                    continue
                        else:
                            print("Incorrect password.")
                    else:
                        print("No username match in database.")
                        client_socket.close()

                elif action == 'register':
                    username = payload
                    password = payload2
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

    def listen(self, player_id) -> None:
        while True:
            for room in self.rooms:
                player: Player = room.players[player_id]
                if player is None:
                    continue
                room.listen(player_id)

    def update_clients(self) -> None:
        for room in self.rooms:
            room.update_clients()

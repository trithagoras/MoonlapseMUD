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


class TcpServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = None

        self.log: Log = Log()
        self.tick_rate = 100

        pwd: str = os.path.dirname(__file__)
        self.rooms: List[Optional[Room]] = [
            Room(self, os.path.join(pwd, '..', 'maps', 'map.bmp.json'), 100)
        ]

    def start(self):
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

            except Exception as e:
                print(e, file=sys.stderr)
                pass

    def connect_socket(self):
        print("Connecting to socket... ", end='')
        if self.sock:
            self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.ip, self.port))
        self.sock.listen(16)

        print(f"done: {self.sock.getsockname()}")

    def accept_clients(self) -> None:
        while True:
            for room in self.rooms:
                try:
                    client_socket, address = self.sock.accept()
                except socket.error as e:
                    print(f"Socket error while accepting new client ({e})... Trying again.")
                    self.connect_socket()
                    time.sleep(1)
                    continue
                except Exception as e:
                    print(e, file=sys.stderr)
                    continue

                player_id: int = -1
                for index in range(0, len(room.players)):
                    if room.players[index] is None:
                        player_id = index
                        break

                if player_id == -1:
                    try:
                        client_socket.send(bytes('full;', 'utf-8'))
                        client_socket.close()
                        print(f"Connection from {address} rejected.")
                    except Exception as e:
                        print(e, file=sys.stderr)
                        continue

                else:
                    print(f"Connection from {address}. Assigning to player {player_id}")
                    self.log.log(time.time(), f"Player {player_id} has arrived.")
                    init_data = {
                      'id': player_id,
                      'w': room.width,
                      'h': room.height,
                      'walls': room.walls,
                      't': self.tick_rate
                    }

                    try:
                        client_socket.send(bytes(json.dumps(init_data) + ';', 'utf-8'))
                        room.players[player_id] = Player(client_socket, init_data)
                        Thread(target=self.listen, args=(player_id,), daemon=True).start()
                    except Exception as e:
                        print(e)
                        continue

    def listen(self, player_id) -> None:
        while True:
            for room in self.rooms:
                player = room.players[player_id]
                data = ''
                try:
                    while True:
                        data += player.client_socket.recv(1024).decode('utf-8')

                        if data[-1] == ';':
                            break

                except socket.error:
                    room.kick(player_id)
                    break

                try:
                    data = json.loads(data[:-1])
                    action: str = data['a']
                    payload: str = data['p']

                    print(f"Received data from player {player_id}: Action={action}, Payload={payload}")

                    pos = player.state['pos']

                    # Move
                    if action == 'm':
                        if payload == 0 and pos['y'] - 1 > 0 and [pos['x'], pos['y'] - 1] not in room.walls:
                            pos['y'] -= 1
                        if payload == 1 and pos['x'] + 1 < room.width - 1 and [pos['x'] + 1, pos['y']] not in room.walls:
                            pos['x'] += 1
                        if payload == 2 and pos['y'] + 1 < room.height - 1 and [pos['x'], pos['y'] + 1] not in room.walls:
                            pos['y'] += 1
                        if payload == 3 and pos['x'] - 1 > 0 and [pos['x'] - 1, pos['y']] not in room.walls:
                            pos['x'] -= 1

                    elif action == 'c':
                        payload = payload.replace(';', '\\;')
                        payload = payload.replace('\\\\;', '\\;')
                        self.log.log(time.time(), f"Player {player_id} says: {payload}")

                except Exception as e:
                    print(e, file=sys.stderr)
                    continue

    def update_clients(self) -> None:
        for room in self.rooms:
            players = []

            for index in range(0, len(room.players)):
                player = room.players[index]
                players.append(player.state if player else None)

            for player in room.players:
                if player:
                    try:
                        player.client_socket.send(bytes(json.dumps({
                            'p': players,
                            'l': self.log.latest
                        }) + ";", 'utf-8'))
                    except socket.error:
                        room.kick(player.player_id)
                        continue
                    except Exception as e:
                        print(e, file=sys.stderr)
                        continue

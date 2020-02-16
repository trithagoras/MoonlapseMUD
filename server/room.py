import json
import socket
import sys
import time
from threading import Thread
from typing import *
from player import Player


class Room:
    def __init__(self, tcpsrv, room_map, capacity):
        self.walls: set = set()
        self.players: List[Optional[Player]] = []
        self.capacity = capacity

        self.tcpsrv = tcpsrv

        try:
            self.tcpsrv.connect_socket()
        except Exception as e:
            print(e, file=sys.stderr)

        with open(room_map) as data:
            map_data = json.load(data)
            self.walls = map_data['walls']
            self.width, self.height = map_data['size']

        # Create player spots in game object
        for index in range(0, self.capacity):
            self.players.append(None)

    def kick(self, player_id: int):
        username = self.players[player_id].username
        self.players[player_id].disconnect()
        self.tcpsrv.log.log(time.time(), f"{username} has departed.")
        self.players[player_id] = None
        print(f"Kicked {username}")

    def spawn(self, player: Player):
        player_id: int = -1
        for index in range(self.capacity):
            if self.players[index] is None:
                player_id = index
                break

        if player_id == -1:
            player.client_socket.send(bytes('full;', 'utf-8'))
            player.client_socket.close()
            print(f"Connection from {player.client_socket} rejected.")

        else:
            print(f"Connection from {player.client_socket}. Assigning to player {player_id}")
            self.tcpsrv.log.log(time.time(), f"{player.username} has arrived.")
            init_data = {
                'id': player_id,
                'w': self.width,
                'h': self.height,
                'walls': self.walls,
                't': self.tcpsrv.tick_rate
            }

            player.client_socket.send(bytes(json.dumps(init_data) + ';', 'utf-8'))
            player.init_data(init_data)

            init_pos = self.tcpsrv.database.get_player_pos(player)
            player.spawn_player(init_pos)

            if init_pos == (None, None):
                pos = player.state['pos']
                self.tcpsrv.database.update_player_pos(player, pos['x'], pos['y'])

            self.players[player_id] = player
            Thread(target=self.tcpsrv.listen, args=(player_id,), daemon=True).start()
            
    def listen(self, player_id) -> None:
        player = self.players[player_id]
        data = ''
        try:
            while True:
                data += player.client_socket.recv(1024).decode('utf-8')

                if data[-1] == ';':
                    break

        except socket.error:
            self.kick(player_id)
            return

        try:
            data = json.loads(data[:-1])
            action: str = data['a']
            payload: str = data['p']
            try:
                payload2 = data['p2']
            except KeyError:
                payload2 = ''

            print(f"Received data from player {player_id}: Action={action}, Payload={payload}:{payload2}")

            pos = player.state['pos']

            # Move
            if action == 'm':
                if payload == 0 and pos['y'] - 1 > 0 and [pos['x'], pos['y'] - 1] not in self.walls:
                    pos['y'] -= 1
                if payload == 1 and pos['x'] + 1 < self.width - 1 and [pos['x'] + 1, pos['y']] not in self.walls:
                    pos['x'] += 1
                if payload == 2 and pos['y'] + 1 < self.height - 1 and [pos['x'], pos['y'] + 1] not in self.walls:
                    pos['y'] += 1
                if payload == 3 and pos['x'] - 1 > 0 and [pos['x'] - 1, pos['y']] not in self.walls:
                    pos['x'] -= 1

                self.tcpsrv.database.update_player_pos(player, pos['x'], pos['y'])

            # Chat
            elif action == 'c':
                payload = payload.replace(';', '\\;')
                payload = payload.replace('\\\\;', '\\;')
                self.tcpsrv.log.log(time.time(), f"{player.username} says: {payload}")

            elif action == 'bye':
                self.kick(player_id)
                return

        except Exception as e:
            print(e, file=sys.stderr)

    def update_clients(self) -> None:
        players = []

        for index in range(0, len(self.players)):
            player = self.players[index]
            players.append(player.state if player else None)

        for player in self.players:
            self.send(player, {
                'p': players,
                'l': self.tcpsrv.log.latest
            })

    def send(self, player, data):
        if player:
            try:
                player.client_socket.send(bytes(json.dumps(data) + ";", 'utf-8'))
            except socket.error:
                self.kick(player.player_id)
            except Exception as e:
                print(e, file=sys.stderr)

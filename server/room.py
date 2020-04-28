import json
import socket
import sys
import time
from threading import Thread
from typing import *
import traceback

# Add server to path
import os
from pathlib import Path # if you haven't already done so
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

# Remove server from path
try:
    sys.path.remove(str(parent))
except ValueError:
    print("Error: Removing parent from path, already gone. Traceback: ")
    print(traceback.format_exc())

from networking import packet as pack
from networking import models


class Room:
    def __init__(self, tcpsrv, room_map, capacity):
        self.walls: set = set()
        self.players: List[Optional[models.Player]] = []
        self.capacity = capacity

        self.tcpsrv = tcpsrv

        try:
            self.tcpsrv.connect_socket()
        except Exception as e:
            print("Error: Traceback: ", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)

        with open(room_map) as data:
            map_data = json.load(data)
            self.walls = map_data['walls']
            self.width, self.height = map_data['size']

        # Create player spots in game object
        for index in range(0, self.capacity):
            self.players.append(None)

    def kick(self, player_id: int, reason='Not given'):
        player = self.players[player_id]
        if player is not None:
            player.disconnect()
            username = self.players[player_id].username
            self.tcpsrv.log.log(time.time(), f"{username} has departed. Reason: {reason}")
            print(f"Kicked {username}. Reason: {reason}")
        else:
            self.tcpsrv.log.log(time.time(), f"Player {player_id} has departed. Reason: {reason}")
            print(f"Kicked player {player_id}. Reason: {reason}")
        self.players[player_id] = None

    def spawn(self, player: models.Player):
        print("Trying to spawn player:", player)
        player_id: int = -1
        for index in range(self.capacity):
            if self.players[index] is None:
                player_id = index
                break
        print("Assigned player", player, "id", player_id)
        if player_id == -1:
            self.send(player, pack.ServerRoomFullPacket())
            player.client_socket.close()
            print(f"Connection from {player.client_socket} rejected.")
            return

        else:
            print(f"Connection from {player.client_socket}. Assigning to player {player_id}")
            self.tcpsrv.log.log(time.time(), f"{player.username} has arrived.")

            self.send(player, pack.ServerRoomPlayerPacket(player))
            player.player_id = player_id
            self.send(player, pack.ServerRoomSizePacket(self.height, self.width))
            self.send(player, pack.ServerRoomGeometryPacket(self.walls))
            self.send(player, pack.ServerRoomTickRatePacket(self.tcpsrv.tick_rate))
    
            init_pos = self.tcpsrv.database.get_player_pos(player)
            player.spawn_player(init_pos, self)

            if init_pos == (None, None):
                pos = player.position
                self.tcpsrv.database.update_player_pos(player, pos[0], pos[1])

            self.players[player_id] = player
            Thread(target=self.tcpsrv.listen, args=(player,), daemon=True).start()

    def listen(self, player: models.Player) -> None:
        print(f"Waiting for data from player {player}...")
        if player is None:
            print("Player not found. Stop listening.")
            return
        print(f"Got player: {player.username}. ")
        
        packet: pack.Packet = pack.receivepacket(player.client_socket)

        print(f"Received data from player {player}: {packet}")

        # Move
        if isinstance(packet, pack.MovePacket):
            pos = player.position
            dir = packet.payloads[0].value
            if dir == 'u' and pos[0] - 1 > 0 and [pos[0] - 1, pos[1]] not in self.walls:
                pos[0] -= 1
            if dir == 'r' and pos[1] + 1 < self.width - 1 and [pos[0], pos[1] + 1] not in self.walls:
                pos[1] += 1
            if dir == 'd' and pos[0] + 1 < self.height - 1 and [pos[0] + 1, pos[1]] not in self.walls:
                pos[0] += 1
            if dir == 'l' and pos[1] - 1 > 0 and [pos[0], pos[1] - 1] not in self.walls:
                pos[1] -= 1
            self.tcpsrv.database.update_player_pos(player, pos[0], pos[1])
        # Chat
        elif isinstance(packet, pack.ChatPacket):
            self.tcpsrv.log.log(time.time(), f"{player.username} says: {packet.payloads[0].value}")
        # Disconnect
        elif isinstance(packet, pack.DisconnectPacket):
            self.kick(player, reason="Player said goodbye.")
            return

    def update_clients(self) -> None:
        for player in self.players:
            if player is not None:
                self.send(player, pack.ServerLogPacket(self.tcpsrv.log.latest))

    def send(self, player: models.Player, packet: pack.Packet):
        if player:
            try:
                pack.sendpacket(player.client_socket, packet)
            except socket.error:
                print("Error: Socket error. Traceback: ", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                self.kick(player.player_id, reason=f"Server couldn't send packet {packet} to client socket.")
            except Exception:
                print("Error: Traceback: ", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)

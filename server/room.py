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
    pass

from networking import packet as pack
from networking.payload import StdPayload as stdpay
from networking import models


class Room:
    def __init__(self, tcpsrv, room_map, capacity):
        self.walls: set = set()
        self.player_sockets: Dict[models.Player, socket.socket] = {}
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
            self.height, self.width = map_data['size']


    def kick(self, player: models.Player, reason='Not given'):
            self.player_sockets[player].close()
            self.player_sockets.pop(player)
            self.tcpsrv.log.log(f"{player.get_username()} has departed. Reason: {reason}")
            print(f"Kicked {player.get_username()}. Reason: {reason}")

    def spawn(self, client_socket: socket.socket, username: str):
        print("Trying to spawn player...")

        player: models.Player = models.Player()
        player.assign_username(username)
        print(f"Assigned username: {username}")

        if len(self.player_sockets) >= self.capacity:
            self.send(player, pack.ServerRoomFullPacket())
            client_socket.close()
            print(f"Connection from {player} rejected.")
            return

        player_id: int = len(self.player_sockets)
        player.assign_id(player_id)

        print(f"Connection from {player}. Assigned player id: {player_id}")
        self.tcpsrv.log.log(f"{player.get_username()} has arrived.")

        init_pos = self.tcpsrv.database.get_player_pos(player)
        player.assign_location(list(init_pos), self)

        if init_pos == (None, None):
            pos = player.get_position()
            self.tcpsrv.database.update_player_pos(player, pos[0], pos[1])

        self.player_sockets[player] = client_socket

        # Send initial room data to the player connecting
        self.send(player, pack.ServerRoomPlayerPacket(player))
        self.send(player, pack.ServerRoomSizePacket(self.height, self.width))
        self.send(player, pack.ServerRoomGeometryPacket(self.walls))
        self.send(player, pack.ServerRoomTickRatePacket(self.tcpsrv.tick_rate))
        
        Thread(target=self.listen, args=(player,), daemon=True).start()

    def listen(self, player: models.Player) -> None:
        while True:
            packet: pack.Packet = pack.receivepacket(self.player_sockets[player])
            print("Received packet", packet)

            # Move
            if isinstance(packet, pack.MovePacket):
                pay: stdpay = packet.payloads[0]
                pos: Tuple[int] = player.get_position()
                dir = packet.payloads[0].value
                
                # Calculate the desired desination
                dest: List[int] = list(pos)
                if pay == stdpay.MOVE_UP:
                    dest[0] -= 1
                elif pay == stdpay.MOVE_RIGHT:
                    dest[1] += 1
                elif pay == stdpay.MOVE_DOWN:
                    dest[0] += 1
                elif pay == stdpay.MOVE_LEFT:
                    dest[1] -= 1
            
                if self.within_bounds(dest) and dest not in self.walls:
                    player.set_position(dest)

                self.tcpsrv.database.update_player_pos(player, dest[0], dest[1])

            # Chat
            elif isinstance(packet, pack.ChatPacket):
                self.tcpsrv.log.log(f"{player.get_username()} says: {packet.payloads[0].value}")
            
            # Disconnect
            elif isinstance(packet, pack.DisconnectPacket):
                self.kick(player, reason="Player said goodbye.")
                return

    def within_bounds(self, coords: List[int]) -> bool:
        return 0 <= coords[0] < self.height and 0 <= coords[1] < self.width


    def update_clients(self) -> None:
        for player in self.player_sockets.keys():
            self.send(player, pack.ServerLogPacket(self.tcpsrv.log.latest))

            # Send the latest player information
            for p in self.player_sockets.keys():
                    self.send(player, pack.ServerRoomPlayerPacket(p))


    def send(self, player: models.Player, packet: pack.Packet):
        try:
            pack.sendpacket(self.player_sockets[player], packet)
        except socket.error:
            print("Error: Socket error. Traceback: ", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            self.kick(player, reason=f"Server couldn't send packet {packet} to client socket.")
        except Exception:
            print("Error: Traceback: ", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)

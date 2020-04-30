import json
import socket
import sys
import time
from threading import Thread
from typing import *
import traceback

# Add server to path
import os
from pathlib import Path
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
    def __init__(self, tcpsrv, data: str, capacity: int):
        """
        Initialises a room object which is responsible for holding 
        room-specific data and spawning and handling players inside 
        of it.

        :param tcpsrv: The TcpServer object responsible for handling 
                       external connections.
        :param data: A JSON string consisting of room information such 
                     as size and geometry.
        :param capacity: The maximum number of players allowed to join 
                         this room.
        """
        self.tcpsrv = tcpsrv
        self.capacity: int = capacity
        
        self.walls: Set[List[int]] = set()
        self.walls = data['walls']
        self.height, self.width = data['size']

        # Reserve a full map of empty players to reserved sockets
        self.player_sockets: Dict[models.Player, socket.socket] = {}
        for pid in range(self.capacity):
            p = models.Player(pid)
            self.player_sockets[p] = None

    def _kick(self, player: models.Player, reason: str = 'Not given') -> None:
            # Free the player position
            self.player_sockets[player].close()
            self.player_sockets[player] = None

            # Log the event
            self.tcpsrv.log.log(f"{player.get_username()} has departed. Reason: {reason}")
            print(f"Kicked {player.get_username()}. Reason: {reason}")

    def spawn(self, client_socket: socket.socket, username: str) -> None:
        """
        Attempts to initialise a new player in this room from a given connection.
        Once the player has been initialised successfully, the room will listen for 
        packets and handle them appropriately in its own thread.

        Raises RoomFullException if the room is full.

        :param client_socket: The socket for the new player.
        :param username: The username of the user to be tied to the new player.
        :raises RoomFullException: If the room is already full.
        """

        # Try to assign a player id to the new connection
        new_player: Optional[models.Player] = None
        for reserved_player, reserved_socket in self.player_sockets.items():
            if reserved_socket is None:
                new_player = reserved_player

        if new_player is None:
            raise RoomFullException(f"room is at capacity {self.capacity}")
        
        # The room is not full so proceed with setting up the new player
        new_player.assign_username(username)

        init_pos = self.tcpsrv.database.get_player_pos(new_player)
        new_player.assign_location(list(init_pos), self)

        if init_pos == (None, None):
            pos = new_player.get_position()
            self.tcpsrv.database.update_player_pos(new_player, pos[0], pos[1])

        self.player_sockets[new_player] = client_socket

        # Send initial room data to the player connecting
        self.send(new_player, pack.ServerRoomPlayerPacket(new_player))
        self.send(new_player, pack.ServerRoomSizePacket(self.height, self.width))
        self.send(new_player, pack.ServerRoomGeometryPacket(self.walls))
        self.send(new_player, pack.ServerRoomTickRatePacket(self.tcpsrv.tick_rate))

        self.tcpsrv.log.log(f"{new_player.get_username()} has arrived.")
        
        # Begin the loop of handling the new player's requests in a separate thread
        Thread(target=self._handle_player, args=(new_player,), daemon=True).start()

    def _handle_player(self, player: models.Player) -> None:
        sock: socket.socket = self.player_sockets[player]
        while True:
            packet: pack.Packet = pack.receivepacket(sock)
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
            
                if self._within_bounds(dest) and dest not in self.walls:
                    player.set_position(dest)

                self.tcpsrv.database.update_player_pos(player, dest[0], dest[1])

            # Chat
            elif isinstance(packet, pack.ChatPacket):
                self.tcpsrv.log.log(f"{player.get_username()} says: {packet.payloads[0].value}")
            
            # Disconnect
            elif isinstance(packet, pack.DisconnectPacket):
                self._kick(player, reason="Player said goodbye.")
                return

    def _within_bounds(self, coords: List[int]) -> bool:
        return 0 <= coords[0] < self.height and 0 <= coords[1] < self.width

    def update_clients(self) -> None:
        """
        Sends information to each client controlling a player in this room.
        This information can be used by the client to update their displays.
        """
        for player in self.player_sockets.keys():
            self.send(player, pack.ServerLogPacket(self.tcpsrv.log.latest))

            # Send the latest player information
            for p in self.player_sockets.keys():
                if p is not None and p.ready():
                    self.send(player, pack.ServerRoomPlayerPacket(p))


    def send(self, player: models.Player, packet: pack.Packet):
        try:
            pack.sendpacket(self.player_sockets[player], packet)
        except AttributeError:
            # Player is reserved and has no connection
            pass
        except socket.error:
            print("Error: Socket error. Traceback: ", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            self._kick(player, reason=f"Server couldn't send packet {packet} to client socket.")
        except Exception:
            print("Error: Traceback: ", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)


class RoomFullException(Exception):
    pass
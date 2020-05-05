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
import select
import queue


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

        # Keep a packet queue for each player socket so that they can be sent 
        # when the socket is ready for writing
        self.socket_queues: Dict[socket.socket, queue.Queue[pack.Packet]] = {}

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

        # Enqueue initial room data to the player connecting
        self._enqueue(new_player, pack.ServerRoomPlayerPacket(new_player))
        self._enqueue(new_player, pack.ServerRoomSizePacket(self.height, self.width))
        self._enqueue(new_player, pack.ServerRoomGeometryPacket(self.walls))
        self._enqueue(new_player, pack.ServerRoomTickRatePacket(self.tcpsrv.tick_rate))

        self.tcpsrv.log.log(f"{new_player.get_username()} has arrived.")
        
    def _handle_packet(self, packet: pack.Packet, sendingPlayer: models.Player) -> None:
        print(f"Received packet {packet} from player {sendingPlayer}")

        if packet is None:
            return

        # Move
        if isinstance(packet, pack.MovePacket):
            pay: stdpay = packet.payloads[0]
            pos: Tuple[int] = sendingPlayer.get_position()
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
                sendingPlayer.set_position(dest)

            self.tcpsrv.database.update_player_pos(sendingPlayer, dest[0], dest[1])

        # Chat
        elif isinstance(packet, pack.ChatPacket):
            self.tcpsrv.log.log(f"{sendingPlayer.get_username()} says: {packet.payloads[0].value}")
        
        # Disconnect
        elif isinstance(packet, pack.DisconnectPacket):
            self._kick(sendingPlayer, reason="Player said goodbye.")
            return

    def _within_bounds(self, coords: List[int]) -> bool:
        return 0 <= coords[0] < self.height and 0 <= coords[1] < self.width

    def update_clients(self) -> None:
        """
        Sends information to each client controlling a player in this room.
        This information can be used by the client to update their displays.
        """
        if not self._get_readysockets():
            print("No clients ready to update")
            return
        
        # Keep track of which player sockets are ready to read from, write to, or throw exceptions
        readySockets: List[socket.socket] = self._get_readysockets()
        queueSockets: List[socket.socket] = self.socket_queues.keys()
        readables, writeables, exceptionals = select.select(readySockets, queueSockets, readySockets, 1 / self.tcpsrv.tick_rate)

        for s in readables:
            sendingPlayer = self._get_player_from_socket(s)

            # Queue the player information about the room and listen for their requests
            self._enqueue(sendingPlayer, pack.ServerLogPacket(self.tcpsrv.log.latest))

            # Enqueue the latest player information
            for p in self.player_sockets.keys():
                if p is not None and p.ready():
                    self._enqueue(sendingPlayer, pack.ServerRoomPlayerPacket(p))

            readpacket: Optional[pack.Packet] = pack.receivepacket(s)
            self._handle_packet(readpacket, sendingPlayer)
        
        for s in writeables:
            try:
                nextPacket: pack.Packet = self.socket_queues[s].get_nowait()
            except queue.Empty:
                self.socket_queues.pop(s)
            else:
                pack.sendpacket(s, nextPacket)

        for s in exceptionals:
            self._kick(self._get_player_from_socket(s))

    def _enqueue(self, player: models.Player, packet: pack.Packet):
        s: socket.socket = self.player_sockets[player]
        if s is None:
            return  
        try:
            self.socket_queues[s].put(packet)
        except KeyError:
            self.socket_queues[s] = queue.Queue()
            self.socket_queues[s].put(packet)
        print(f"Enqueued player {player.get_username()} with packet {packet}.")

    def _get_readysockets(self) -> List[socket.socket]:
        return [s for s in self.player_sockets.values() if s is not None]

    def _kick(self, player: models.Player, reason: str = 'Not given') -> None:
            playersocket = self.player_sockets[player]

            # Discard of the player's queued packets
            try:
                self.socket_queues.pop(playersocket)
            except KeyError:
                pass

            # Free the player position
            self.player_sockets[player].close()
            self.player_sockets[player] = None

            # Log the event
            self.tcpsrv.log.log(f"{player.get_username()} has departed. Reason: {reason}")
            print(f"Kicked {player.get_username()}. Reason: {reason}")

    def _get_player_from_socket(self, playerSocket: socket.socket) -> models.Player:
        for p, s in self.player_sockets.items():
            if s == playerSocket:
                return p

        raise ValueError(f"socket {playerSocket} does not belong to a player in this room")


class RoomFullException(Exception):
    pass
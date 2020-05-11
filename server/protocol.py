from twisted.protocols.basic import NetstringReceiver
from twisted.protocols.basic import IncompleteNetstring
from twisted.protocols.basic import NetstringParseError
from twisted.internet.protocol import Protocol
from twisted.internet.defer import Deferred

from server import database
from networking import packet
from networking import models

from typing import *
import time
import json
import os


class Moonlapse(NetstringReceiver):
    """
    A protocol that sends and receives netstrings. See http://cr.yp.to/proto/netstrings.txt for the 
    specification of netstrings.

    The constructing and sending of netstrings is handled by the networking.packet package, as Moonlapse 
    has its own Packet class which encapsulates packet types and payloads as netstrings for communication 
    between protocols and clients.

    The self.stringReceived method handles received netstrings. This method is called with the netstring 
    payload as a single argument whenever a complete netstring is received. This method should never be 
    called external to the underlying twisted.protocols.basic.NetstringReceiver implementation. It is fired 
    every data is received to this protocol.

    The self.sendPacket method 

    The self.processPacket method
    """
    def __init__(self, database: database.Database, users: Dict[str, 'Moonlapse']):
        super().__init__()
        self.database: Database = database
        self.users: Dict[str, 'Moonlapse'] = users
        self.username: str = None
        self.password: str = None
        self.player: models.Player = None
        self.state: function = self._GETENTRY

        pwd: str = os.path.dirname(__file__)
        room_data_filename: str = os.path.join(pwd, '..', 'maps', 'map.bmp.json')
        self.room_data: Dict[str, object] = None
        with open(room_data_filename, 'r') as room_data_file:
            self.room_data = json.load(room_data_file)

    def connectionMade(self) -> None:
        super().__init__()
        # print(f"[{self.username}]: New connection")
        servertime: str = time.strftime('%d %B, %Y %R %p', time.gmtime())
        self.sendPacket(packet.WelcomePacket(f"Welcome to MoonlapseMUD - Server time: {servertime}"))

    def connectionLost(self, reason="unspecified") -> None:
        super().__init__()
        # print(f"[{self.username}]: Lost connection")
        if self.username in self.users:
            del self.users[self.username]
            print(f"[{self.username}]: Deleted self from users list")
            for protocol in self.users.values():
                print(f"[{self.username}]: Sending disconnect to {protocol.username}")
                protocol.processPacket(packet.DisconnectPacket(self.player))

    def stringReceived(self, string) -> None:
        """
        Processes data sent from this protocol's client.
        This should never be called directly. It's handled by NetStringReceiver 
        on dataReceived.
        """
        p: packet.Packet = packet.frombytes(string)
        print(f"[{self.username}]: Received packet from my client {p}")
        self.state(p)

    def sendPacket(self, p: packet.Packet) -> None:
        """
        Sends a packet to this protocol's client. 
        Call this to communicate information back to the game client application.
        """
        print(f"[{self.username}]: Sending to this my client", p)
        self.transport.write(p.tobytes())

    def processPacket(self, p: packet.Packet) -> None:
        """
        Processes packets sent to this protocol from another protocol.
        Call this to communicate with other protocols connected to the main server.
        """
        print(f"[{self.username}]: Received packet from another protocol {p}")
        self.state(p)


    def _PLAY(self, p: packet.Packet) -> None:
        """
        Handles packets received when this protocol is in the PLAY state.
        This should never be called directly and is instead handled by 
        stringReceived.
        """
        if isinstance(p, packet.MovePacket):
            self.move(p)
        elif isinstance(p, packet.ChatPacket):
            self.chat(p)
        elif isinstance(p, packet.HelloPacket):
            self.welcome(p)
        elif isinstance(p, packet.DisconnectPacket):
            self.disconnect(p)


    def _GETENTRY(self, p: Union[packet.LoginPacket, packet.RegisterPacket]) -> None:
        """
        Handles packets received when this protocol is in the GETENTRY state.
        This should never be called directly and is instead handled by 
        stringReceived.
        """
        username: str = p.payloads[0].value
        password: str = p.payloads[1].value

        if isinstance(p, packet.LoginPacket):
            self._handle_login(username, password)
        elif isinstance(p, packet.RegisterPacket):
            self._handle_registration(username, password)

    def _handle_login(self, username: str, password: str) -> None:
        """
        Handles a login packet by doing the following asynchronously:
        1. Check if the given username is already connected to the server
        2. Check if the given username exists in the database
        3. Check if the given password is correct for the given username
        4. Initialises the new player in this protocol by setting some instance 
           variables
        5. Establishes the new player in the room and sends information back to the 
           game client

        If an error occurs at any point in the process, it is sent as a Deny Packet back 
        to the client with an appropriate error message.
        """
        if self.username in self.users.keys():
            self.sendPacket(packet.DenyPacket("You are already inhabiting this realm"))
            return

        self.database.user_exists(username
        ).addCallbacks(
            callback = self._check_password_correct, 
            callbackArgs = (username, password),
            errback = lambda e: self.sendPacket(packet.denyPacket(e.getErrorMessage())) # Catch user_exists
        ).addCallbacks(
            callback = self._initialise_player, 
            callbackArgs=(username,), 
            errback = lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage())) # Catch check_password_correct
        ).addCallbacks(
            callback = self._establish_player_in_world, 
            errback = lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage()))  # Catch initialise_new_player
        )

    def _check_password_correct(self, user_exists: List[Tuple[bool]], username: str, password: str) -> Deferred:
        if not user_exists[0][0]:
            raise EntryError("I don't know anybody by that name")

        return self.database.password_correct(username, password)

    def _initialise_player(self, password_correct: List[Tuple[bool]], username: str) -> Deferred:
        if not password_correct[0][0]:
            raise EntryError("Incorrect password")
        
        self.sendPacket(packet.OkPacket())
        
        self.username = username
        
        self.users[self.username] = self

        self.player = models.Player(len(self.users))
        self.player.assign_username(self.username)
        
        return self.database.get_player_pos(self.player)

    def _establish_player_in_world(self, init_pos: List[Tuple[int]]) -> None:
        print(f"[{self.username}]: Got", init_pos)
        init_pos = init_pos[0]
        self.player.assign_location(list(init_pos), self.room_data['walls'], *self.room_data['size'])

        if init_pos == (None, None):
            pos = self.player.get_position()
            self.database.update_player_pos(self.player, pos[0], pos[1])

        self.sendPacket(packet.ServerRoomSizePacket(*self.room_data['size']))
        self.sendPacket(packet.ServerRoomGeometryPacket(self.room_data['walls']))
        self.sendPacket(packet.ServerRoomTickRatePacket(100))
        self.sendPacket(packet.ServerRoomPlayerPacket(self.player))

        for protocol in self.users.values():
            if protocol != self:
                protocol.processPacket(packet.HelloPacket(self.player))

        self.state = self._PLAY

    def _handle_registration(self, username: str, password: str) -> None:
        """
        Handles a registration packet by doing the following asynchronously:
        1. Check if the given username does not already exist in the database
        2. Write the new username and password into the database
        3. Tell the client the registration was successful

        If an error occurs at any point in the process, it is sent as a Deny Packet back 
        to the client with an appropriate error message.
        """
        self.database.user_exists(username
        ).addCallbacks(
            callback = self._register_user, 
            callbackArgs = (username, password),
            errback = lambda e: self.sendPacket(packet.denyPacket(e.getErrorMessage()))  # Catch user_exists
        ).addCallbacks(
            callback = lambda _: self.sendPacket(packet.OkPacket()),
            errback = lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage()))  # Catch register_user
        )

    def _register_user(self, user_exists: List[Tuple[bool]], username: str, password: str) -> Deferred:
        if user_exists[0][0]:
            raise EntryError(f"Somebody else already goes by that name")
        
        return self.database.register_user(username, password)

    def chat(self, p: packet.ChatPacket):
        message: str = f"{self.username} says: {p.payloads[0].value}"
        if message.strip() != '':
            for name, protocol in self.users.items():
                protocol.sendPacket(packet.ChatPacket(message))

    def move(self, p: packet.MovePacket):
        pos: Tuple[int] = self.player.get_position()

        # Calculate the desired desination
        dest: List[int] = list(pos)
        if isinstance(p, packet.MoveUpPacket):
            dest[0] -= 1
        elif isinstance(p, packet.MoveRightPacket):
            dest[1] += 1
        elif isinstance(p, packet.MoveDownPacket):
            dest[0] += 1
        elif isinstance(p, packet.MoveLeftPacket):
            dest[1] -= 1

        if self._within_bounds(dest) and dest not in self.room_data['walls']:
            self.player.set_position(dest)
            d: Deferred = self.database.update_player_pos(self.player, dest[0], dest[1])

            for name, protocol in self.users.items():
                protocol.sendPacket(packet.ServerRoomPlayerPacket(self.player))
        else:
            self.sendPacket(packet.DenyPacket("can't move there"))

    def _within_bounds(self, coords: List[int]) -> bool:
        max_height, max_width = self.room_data['size']
        return 0 <= coords[0] < max_height and 0 <= coords[1] < max_width

    def welcome(self, p: packet.HelloPacket):
        new_player: models.Player = p.payloads[0].value
        new_protocol: 'Moonlapse' = None

        # Get the protocol which sent the packet
        for protocol in self.users.values():
            if protocol.player == new_player:
                new_protocol = protocol
                break
        
        # Return if no match found
        if not new_protocol:
            print(f"[{self.player.get_username()}] Could not find protocol attached to new player to welcome ({new_player.get_username()})")
            return

        # Send the client player information for the newly connecting protocol
        self.sendPacket(packet.ServerRoomPlayerPacket(new_player))
        
        # Send the newly connecting protocol information for this protocol's player
        new_protocol.sendPacket(packet.ServerRoomPlayerPacket(self.player))
        print(f"[{self.player.get_username()}] Welcomed new player {new_player.get_username()}")

    def disconnect(self, p: packet.DisconnectPacket):
        departing_player: models.Player = p.payloads[0].value
        self.sendPacket(p)

class EntryError(Exception):
    pass

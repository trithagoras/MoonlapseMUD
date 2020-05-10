from twisted.protocols.basic import NetstringReceiver
from twisted.protocols.basic import IncompleteNetstring
from twisted.protocols.basic import NetstringParseError
from twisted.internet.protocol import Protocol
from twisted.internet.defer import Deferred

from server import database
from networking import packet
from networking import models
from networking.payload import StdPayload

from typing import *
import time
import json
import os


class Moonlapse(NetstringReceiver):
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

    def connectionMade(self):
        super().__init__()
        # print(f"[{self.username}]: New connection")
        servertime: str = time.strftime('%d %B, %Y %R %p', time.gmtime())
        self.sendPacket(packet.WelcomePacket(f"Welcome to MoonlapseMUD - Server time: {servertime}"))

    def connectionLost(self, reason="unspecified"):
        super().__init__()
        # print(f"[{self.username}]: Lost connection")
        if self.username in self.users:
            del self.users[self.username]
            print(f"[{self.username}]: Deleted self from users list")
            for protocol in self.users.values():
                print(f"[{self.username}]: Sending disconnect to {protocol.username}")
                protocol.processPacket(packet.DisconnectPacket(self.player))

    def stringReceived(self, string):
        """
        Processes data sent from this protocol's client.
        """
        p: packet.Packet = packet.frombytes(string)
        print(f"[{self.username}]: Received packet from my client {p}")
        self.state(p)

    def sendPacket(self, p: packet.Packet):
        """
        Sends a packet to this protocol's client.
        """
        print(f"[{self.username}]: Sending to this my client", p)
        self.transport.write(p.tobytes())

    def processPacket(self, p: packet.Packet):
        """
        Processes packets sent to this protocol from another protocol.
        """
        print(f"[{self.username}]: Received packet from another protocol {p}")
        self.state(p)


    def _PLAY(self, p: packet.Packet):
        if isinstance(p, packet.MovePacket):
            self.move(p)
        elif isinstance(p, packet.ChatPacket):
            self.chat(p)
        elif isinstance(p, packet.HelloPacket):
            self.welcome(p)


    def _GETENTRY(self, p: Union[packet.LoginPacket, packet.RegisterPacket]):
        username: str = p.payloads[0].value
        password: str = p.payloads[1].value

        if isinstance(p, packet.LoginPacket):
            self.handle_login(username, password)
        elif isinstance(p, packet.RegisterPacket):
            self.handle_register(username, password)

    def handle_login(self, username: str, password: str):
        if self.username in self.users.keys():
            self.sendPacket(packet.DenyPacket("You are already inhabiting this realm"))
            return

        self.database.user_exists(username
        ).addCallbacks(
            callback = self.check_password_correct, 
            callbackArgs = (username, password),
            errback = lambda e: self.sendPacket(packet.denyPacket(e.getErrorMessage())) # Catch user_exists
        ).addCallbacks(
            callback = self.initialise_new_player, 
            callbackArgs=(username,), 
            errback = lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage())) # Catch check_password_correct
        ).addCallbacks(
            callback = self.process_new_player_init_pos, 
            errback = lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage()))  # Catch initialise_new_player
        )

    def check_password_correct(self, user_exists: List[Tuple[bool]], username: str, password: str):
        if not user_exists[0][0]:
            raise EntryError("I don't know anybody by that name")

        return self.database.password_correct(username, password)

    def initialise_new_player(self, password_correct: List[Tuple[bool]], username: str):
        if not password_correct[0][0]:
            raise EntryError("Incorrect password")
        
        self.sendPacket(packet.OkPacket())
        
        self.username = username
        
        self.users[self.username] = self

        self.player = models.Player(len(self.users))
        self.player.assign_username(self.username)
        
        return self.database.get_player_pos(self.player)

    def process_new_player_init_pos(self, init_pos: List[Tuple[int]]):
        print(f"[{self.username}]: Got", init_pos)
        init_pos = init_pos[0]
        self.player.assign_location(list(init_pos), self.room_data['walls'], *self.room_data['size'])

        if init_pos == (None, None):
            pos = self.player.get_position()
            self.database.update_player_pos(self.player, pos[0], pos[1]).addCallback(self.dboperation_done)

        self.sendPacket(packet.ServerRoomSizePacket(*self.room_data['size']))
        self.sendPacket(packet.ServerRoomGeometryPacket(self.room_data['walls']))
        self.sendPacket(packet.ServerRoomTickRatePacket(100))
        self.sendPacket(packet.ServerRoomPlayerPacket(self.player))

        for protocol in self.users.values():
            if protocol != self:
                protocol.processPacket(packet.HelloPacket(self.player))

        self.state = self._PLAY

    def handle_register(self, username: str, password: str):
        self.database.user_exists(username
        ).addCallbacks(
            callback = self.register_user, 
            callbackArgs = (username, password),
            errback = lambda e: self.sendPacket(packet.denyPacket(e.getErrorMessage()))  # Catch user_exists
        ).addCallbacks(
            callback = lambda _: self.sendPacket(packet.OkPacket()),
            errback = lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage()))  # Catch register_user
        )

    def register_user(self, user_exists: List[Tuple[bool]], username: str, password: str):
        if user_exists[0][0]:
            raise EntryError(f"Somebody else already goes by that name")
        
        return self.database.register_user(username, password)

    def dboperation_done(self, result):
        # print(f"[{self.username}]: Done")
        return

    def proceed_to_game(self, username: str):
        pass

    def chat(self, p: packet.ChatPacket):
        message: str = f"{self.username} says: {p.payloads[0].value}"
        if message.strip() != '':
            for name, protocol in self.users.items():
                protocol.sendPacket(packet.ChatPacket(message))

    def move(self, p: packet.MovePacket):
        player: models.Player = p.payloads[0].value
        direction: StdPayload = p.payloads[1]

        pos: Tuple[int] = player.get_position()
        # Calculate the desired desination
        dest: List[int] = list(pos)
        if direction == StdPayload.MOVE_UP:
            dest[0] -= 1
        elif direction == StdPayload.MOVE_RIGHT:
            dest[1] += 1
        elif direction == StdPayload.MOVE_DOWN:
            dest[0] += 1
        elif direction == StdPayload.MOVE_LEFT:
            dest[1] -= 1

        if self._within_bounds(dest) and dest not in self.room_data['walls']:
            player.set_position(dest)
            d: Deferred = self.database.update_player_pos(player, dest[0], dest[1])
            d.addCallback(self.dboperation_done)

            for name, protocol in self.users.items():
                protocol.sendPacket(packet.ServerRoomPlayerPacket(player))
        else:
            self.sendPacket(packet.DenyPacket("can't move there"))

    def _within_bounds(self, coords: List[int]) -> bool:
        max_height, max_width = self.room_data['size']
        return 0 <= coords[0] < max_height and 0 <= coords[1] < max_width

    def welcome(self, p):
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



class EntryError(Exception):
    pass
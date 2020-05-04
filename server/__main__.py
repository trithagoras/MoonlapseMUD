from twisted.protocols.basic import NetstringReceiver, IncompleteNetstring, NetstringParseError
from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.internet.defer import Deferred
from twisted.internet import reactor
from typing import *
import time
import json

# Add to path
import os
import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from server.database import Database
from networking import packet
from networking import models
from networking.payload import StdPayload

# Remove from path
try:
    sys.path.remove(str(parent))
except ValueError:
    pass

class Moonlapse(NetstringReceiver):
    def __init__(self, database: Database, users: Dict[str, 'Moonlapse']):
        super().__init__()
        self.database: Database = database
        self.users: Dict[str, 'Moonlapse'] = users
        self.username: str = None
        self.password: str = None
        self.player: models.Player = None
        self.state: function = self._GETLOGIN

        pwd: str = os.path.dirname(__file__)
        room_data_filename: str = os.path.join(pwd, '..', 'maps', 'map.bmp.json')
        self.room_data: Dict[str, object] = None
        with open(room_data_filename, 'r') as room_data_file:
            self.room_data = json.load(room_data_file)

    def connectionMade(self):
        super().__init__()
        print("New connection")
        servertime: str = time.strftime('%d %B, %Y %R %p', time.gmtime())
        self.sendPacket(packet.WelcomePacket(f"Welcome to MoonlapseMUD - Server time: {servertime}"))

    def connectionLost(self, reason="unspecified"):
        super().__init__()
        print("Lost connection")
        if self.username in self.users:
            del self.users[self.username]
            for name, protocol in self.users.items():
                if protocol != self:
                    protocol.sendPacket(packet.ChatPacket(f"{self.username} has departed..."))

    def stringReceived(self, string):
        print(f"Received string: {string}")
        p: packet.Packet = packet.frombytes(string)
        self.state(p)

    def dataReceived(self, data):
        print(f"Received data: {data}")
        return super().dataReceived(data)

    def _PLAY(self, p: Union[packet.MovePacket, packet.ChatPacket]):
        if isinstance(p, packet.MovePacket):
            self.move(p)
        elif isinstance(p, packet.ChatPacket):
            self.chat(p)

    def _GETLOGIN(self, p: packet.LoginPacket):
        if not isinstance(p, packet.LoginPacket):
            return
        
        self.username: str = p.payloads[0].value
        self.password: str = p.payloads[1].value
        
        self.database.user_exists(self.username).addCallback(self.check_user_exists)

    def check_user_exists(self, result):
        if self.username in self.users.keys() or False in result:
            self.sendPacket(packet.DenyPacket("user already connected"))
            return
        
        self.database.password_correct(self.username, self.password).addCallback(self.check_password_correct)

    def check_password_correct(self, result):
        if False in result:
            self.sendPacket(packet.DenyPacket("incorrect password for user"))
            return

        self.sendPacket(packet.OkPacket())
        self.users[self.username] = self

        for name, protocol in self.users.items():
            protocol.sendPacket(packet.ChatPacket(f"{self.username} has arrived!"))

        self.player = models.Player(len(self.users))
        self.player.assign_username(self.username)
        
        self.database.get_player_pos(self.player).addCallback(self.get_player_init_pos)

    def get_player_init_pos(self, result):
        print("get_player_init_pos ->", result)
        init_pos = result[0]
        self.player.assign_location(list(init_pos), self.room_data['walls'], *self.room_data['size'])

        if init_pos == (None, None):
            pos = self.player.get_position()
            self.database.update_player_pos(self.player, pos[0], pos[1]).addCallback(self.dboperation_done)

        self.sendPacket(packet.ServerRoomSizePacket(*self.room_data['size']))
        self.sendPacket(packet.ServerRoomPlayerPacket(self.player))
        self.sendPacket(packet.ServerRoomGeometryPacket(self.room_data['walls']))
        self.sendPacket(packet.ServerRoomTickRatePacket(100))

        self.state = self._PLAY

    def dboperation_done(self, result):
        print("Done")

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

    def sendPacket(self, p: packet.Packet):
        self.transport.write(p.tobytes())
        # print(f"Sent packet {p}")


class MoonlapseFactory(Factory):
    def __init__(self):
        self.database: Database = Database("./server/connectionstrings.json")
        self.database.connect()
        self.users: Dict[str, 'Moonlapse'] = {}

    def buildProtocol(self, addr):
        return Moonlapse(self.database, self.users)


if __name__ == '__main__':
    reactor.listenTCP(8123, MoonlapseFactory())
    reactor.run()
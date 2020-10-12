from twisted.internet.protocol import Factory
from twisted.internet import reactor
from typing import *
import os

# Required to import from shared modules
import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from server import database
from server import protocol


class MoonlapseServer(Factory):
    def __init__(self, connectionstringspath):
        self.database: database.Database = database.Database(connectionstringspath)
        self.database.connect()

        # Insert the server rooms to the database if they don't already exist
        mapdirs: Tuple[str] = tuple([dirname for dirname in os.listdir('maps') if os.path.isdir(os.path.join('maps', dirname))])
        for mapdir in mapdirs:
            self.database.create_room(mapdir, f"maps/{mapdir}")
            print(f"Added map {mapdir} to the database")

        self.roomnames_users: Dict[Optional[str], [str, protocol.Moonlapse]] = {}

    def buildProtocol(self, addr):
        print("Adding a new client.")
        return protocol.Moonlapse(self, self.database)

    def moveProtocols(self, proto, roomname: str):
        # Remove the player from the old room
        if proto.roomname and proto.username in self.roomnames_users[proto.roomname]:
            self.roomnames_users[proto.roomname].pop(proto.username)

        # Add the player to the new room
        if roomname in self.roomnames_users:
            self.roomnames_users[roomname][proto.username] = proto
        else:
            self.roomnames_users[roomname] = {proto.username: proto}



if __name__ == '__main__':
    pwd: str = os.path.dirname(__file__)

    connectionstringspath: str = os.path.join(pwd, 'connectionstrings.json')

    reactor.listenTCP(42523, MoonlapseServer(connectionstringspath))
    reactor.run()

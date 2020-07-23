from twisted.internet.protocol import Factory
from twisted.internet import reactor
from typing import *
import os
from maps import Room

# Required to import from shared modules
import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from server import database
from server import protocol


class MoonlapseServer(Factory):
    def __init__(self, connectionstringspath, room):
        self.database: database.Database = database.Database(connectionstringspath)
        self.database.connect()

        self.room = room

        self.users: Dict[str, protocol.Moonlapse] = {}

    def buildProtocol(self, addr):
        print("Adding a new client. Sending users:", self.users.items())
        return protocol.Moonlapse(self, self.database, self.users, self.room)


if __name__ == '__main__':
    pwd: str = os.path.dirname(__file__)

    connectionstringspath: str = os.path.join(pwd, 'connectionstrings.json')

    groundmappath = os.path.join(pwd, '..', 'maps', 'tavern_ground.ml')
    solidmappath = os.path.join(pwd, '..', 'maps', 'tavern_solid.ml')
    roofmappath = os.path.join(pwd, '..', 'maps', 'tavern_roof.ml')
    room = Room(groundmappath, solidmappath, roofmappath)


    reactor.listenTCP(42523, MoonlapseServer(connectionstringspath, room))
    reactor.run()

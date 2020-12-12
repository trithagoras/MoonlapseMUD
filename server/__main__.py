from twisted.internet.protocol import Factory
from twisted.internet import reactor
from typing import *
import os
import manage

# Required to import from shared modules
import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from server import protocol
from networking import models
import maps


class MoonlapseServer(Factory):
    def __init__(self):
        # Keep track of room ids and a set of protocols inside, e.g.
        # {
        #   1: {<protocol.Moonlapse object 3>},
        #   3: {<protocol.Moonlapse object 4>, <protocol.Moonlapse object 5>},
        #   None: {<protocol.Moonlapse object 7>}
        # }
        # If the roomname is None, the protocols inside have not logged in to the game yet.
        self.rooms_protocols: Dict[Optional[int], Set[protocol.Moonlapse]] = {None: set()}

        # Insert the server rooms to the database if they don't already exist
        layoutssdir = 'maps/layouts'
        mapdirs: List[str] = [d for d in os.listdir(layoutssdir) if os.path.isdir(os.path.join(layoutssdir, d))]
        for mapdir in mapdirs:
            room_data = maps.Room(mapdir)
            room = models.Room(name=mapdir, ground_data=room_data.grounddata, solid_data=room_data.soliddata, roof_data=room_data.roofdata, height=room_data.height, width=room_data.width)

            room.save()
            if not models.Room.objects.filter(name=room.name):
                print(f"Added map {mapdir} to the database")
            else:
                print(f"Updated map {mapdir} if there were any changes")

    def buildProtocol(self, addr):
        print("Adding a new client.")
        # Give the new client their protocol in the "lobby"
        return protocol.Moonlapse(self, None, self.rooms_protocols[None])

    def moveProtocols(self, proto, dest_roomid: int):
        # Remove the player from the old room
        curr_roomid = None if proto._room is None else proto._room.id
        self.rooms_protocols[curr_roomid].discard(proto)

        # Add the player to the new room
        if dest_roomid not in self.rooms_protocols:
            self.rooms_protocols[dest_roomid] = set()
        self.rooms_protocols[dest_roomid].add(proto)


if __name__ == '__main__':
    PORT: int = 42523
    reactor.listenTCP(PORT, MoonlapseServer())
    print(f"Server listening on port {42523}")
    reactor.run()

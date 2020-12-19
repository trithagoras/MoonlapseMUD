import twisted
import django
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
        layoutssdir = os.path.join(os.path.dirname(os.path.realpath(maps.__file__)), "layouts")
        mapdirs: List[str] = [d for d in os.listdir(layoutssdir) if os.path.isdir(os.path.join(layoutssdir, d))]
        for mapdir in mapdirs:
            room_data = maps.Room(mapdir)
            if not models.Room.objects.filter(name=room_data.name):
                room = models.Room(name=mapdir, ground_data=room_data.grounddata, solid_data=room_data.soliddata, roof_data=room_data.roofdata, height=room_data.height, width=room_data.width)
                room.save()
                print(f"Added map {mapdir} to the database")
            else:
                room = models.Room.objects.get(name=room_data.name)
                room.ground_data = room_data.grounddata
                room.solid_data = room_data.soliddata
                room.roof_data = room_data.roofdata
                room.height = room_data.height
                room.width = room_data.width
                room.save()
                print(f"Updated map {mapdir} if there were any changes")


        tavern_room = models.Room.objects.filter(name="tavern")[0]
        forest_room = models.Room.objects.filter(name="forest")[0]

        if not models.Entity.objects.filter(name='Forest portal 1'):
            forest_portal1_entity = models.Entity(room=forest_room, y=12, x=42, char='O', typename='Portal', name='Forest portal 1')
            forest_portal1 = models.Portal(entity=forest_portal1_entity, linkedy=12, linkedx=25, linkedroom=forest_room)
            forest_portal1_entity.save()
            forest_portal1.save()

        if not models.Entity.objects.filter(name='Forest portal 2'):
            forest_room = models.Room.objects.filter(name="forest")[0]
            forest_portal2_entity = models.Entity(room=forest_room, y=12, x=25, char='O', typename='Portal', name='Forest portal 2')
            forest_portal2 = models.Portal(entity=forest_portal2_entity, linkedy=12, linkedx=42, linkedroom=forest_room)
            forest_portal2_entity.save()
            forest_portal2.save()

        if not models.Entity.objects.filter(name='Forest portal 3'):
            forest_room = models.Room.objects.filter(name="forest")[0]
            forest_portal3_entity = models.Entity(room=forest_room, y=9, x=28, char='O', typename='Portal', name='Forest portal 3')
            forest_portal3 = models.Portal(entity=forest_portal3_entity, linkedy=0, linkedx=15, linkedroom=tavern_room)
            forest_portal3_entity.save()
            forest_portal3.save()

        if not models.Entity.objects.filter(name='Tavern portal'):
            tavern_room = models.Room.objects.filter(name="tavern")[0]
            tavern_portal_entity = models.Entity(room=tavern_room, y=0, x=15, char='O', typename='Portal', name='Tavern portal')
            tavern_portal = models.Portal(entity=tavern_portal_entity, linkedy=9, linkedx=28, linkedroom=forest_room)
            tavern_portal_entity.save()
            tavern_portal.save()

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
    print(f"Starting MoonlapseMUD server")
    PORT: int = 42523
    reactor.listenTCP(PORT, MoonlapseServer())
    print(f"Server listening on port {42523}")
    reactor.run()

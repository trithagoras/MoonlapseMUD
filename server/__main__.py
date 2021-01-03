import twisted
import django
from twisted.internet.protocol import Factory
from twisted.internet import reactor, task
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
from networking import models, packet
import maps


class ProtocolState:
    ANY = 0
    GET_ENTRY = 1
    PLAY = 2
    DISCONNECT = 3


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

        self.weather = "Clear"

        # weather change check
        loop = task.LoopingCall(self.rain_check)
        loop.start(30, False)

    def is_logged_in(self, pid: int) -> bool:
        for room_id in self.rooms_protocols:
            for proto in self.rooms_protocols[room_id]:
                if proto._logged_in:
                    if proto._player:
                        if pid == proto._player.pk:
                            return True
        return False

    def broadcast_to_all(self, p: packet.Packet, state=ProtocolState.ANY):
        for room_id in self.rooms_protocols:
            self.broadcast_to_room(room_id, p, state)

    def broadcast_to_room(self, room_id: int, p: packet.Packet, state=ProtocolState.ANY):

        for proto in self.rooms_protocols[room_id]:
            accept = ((ProtocolState.GET_ENTRY, proto._GETENTRY),
                      (ProtocolState.PLAY, proto._PLAY),
                      (ProtocolState.DISCONNECT, proto._DISCONNECT))

            if (state, proto.state) in accept or state == ProtocolState.ANY:
                proto.sendPacket(p)

    def buildProtocol(self, addr):
        print("Adding a new client.")
        # Give the new client their protocol in the "lobby"
        return protocol.Moonlapse(self, self.rooms_protocols[None])

    def moveProtocols(self, proto, dest_roomid: int):
        # Remove the player from the old room
        curr_roomid = None if proto._room is None else proto._room.id
        self.rooms_protocols[curr_roomid].discard(proto)

        # Add the player to the new room
        if dest_roomid not in self.rooms_protocols:
            self.rooms_protocols[dest_roomid] = set()
        self.rooms_protocols[dest_roomid].add(proto)

    def change_weather(self, new_weather: str):
        print(f"Weather changed from {self.weather} to {new_weather}")

        self.broadcast_to_all(packet.WeatherChangePacket(new_weather), state=ProtocolState.PLAY)
        self.weather = new_weather

        if self.weather == "Rain":
            self.broadcast_to_all(packet.ServerLogPacket("It has begun to rain..."), state=ProtocolState.PLAY)

        elif self.weather == "Clear":
            self.broadcast_to_all(packet.ServerLogPacket("The rain has cleared."), state=ProtocolState.PLAY)

    def rain_check(self):
        # random check here

        if self.weather == "Clear":
            self.change_weather("Rain")

        elif self.weather == "Rain":
            self.change_weather("Clear")


if __name__ == '__main__':
    print(f"Starting MoonlapseMUD server")
    PORT: int = 42523
    reactor.listenTCP(PORT, MoonlapseServer())
    print(f"Server listening on port {42523}")
    reactor.run()

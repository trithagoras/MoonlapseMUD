from twisted.internet import task
from twisted.internet.protocol import Factory
from typing import *

from server import manage, models
import server.protocol as protocol
from networking import packet
import maps


class MoonlapseServer(Factory):
    def __init__(self):
        # all protocols connected to server
        self.connected_protocols: Set[protocol.MoonlapseProtocol] = set()

        # dict of all instances in the game. instance.pk : instance
        self.instances: Dict[int, models.InstancedEntity] = {}
        for instance in models.InstancedEntity.objects.all():
            self.instances[instance.pk] = instance

        self.weather = 'Clear'
        # weather change check
        rainloop = task.LoopingCall(self.rain_check)
        rainloop.start(30, False)

        # save all instances to DB after loop
        dbsaveloop = task.LoopingCall(self.save_all_instances)
        dbsaveloop.start(20, False)     # todo: 20s for testing; obvs should be less often

    def protocols_in_room(self, roomid: int) -> Set[protocol.MoonlapseProtocol]:
        s = set()
        for proto in self.connected_protocols:
            if proto.logged_in and proto.player_instance.room.pk == roomid:
                s.add(proto)
        return s

    def get_proto_by_id(self, entityid: int) -> Optional[protocol.MoonlapseProtocol]:
        for proto in self.connected_protocols:
            if not proto.logged_in:
                return
            if proto.player_info.entity.pk == entityid:
                return proto

    def instances_in_room(self, roomid: int) -> Dict[int, models.InstancedEntity]:
        d = {}
        for key in self.instances:
            if self.instances[key].room_id == roomid:
                d[key] = self.instances[key]
        return d

    def broadcast_to(self, p: packet.Packet, including: Iterable[protocol.MoonlapseProtocol],
                     excluding: Iterable[protocol.MoonlapseProtocol] = tuple(), state='ANY'):
        """
        Sends packets to all protocols specified in "including" except for the ones for the protocols specified in
        "excluding", if any.
        If no protocols are specified in "including", the default behaviour is to send to *all* protocols on the server
        except for the ones specified in "excluding", if any.

        Examples:
            * broadcast(packet.ServerLogPacket("Hello"), excluding=(Josh,)) will send to everyone but Josh
            * broadcast(packet.ServerLogPacket("Hello"), including=(Sue, James)) will send to only Sue and James
            * broadcast(packet.ServerLogPacket("Hello"), including=(Mary,), excluding=(Mary,)) will send to noone
        """
        print(f"Broadcasting {p} to {tuple(p.username for p in including) if including else 'everyone'} "
              f"{'except' + str(tuple(p.username for p in excluding)) if tuple(p.username for p in excluding) else ''}")

        sendto = including
        sendto = {proto for proto in sendto if proto not in excluding and (state == 'ANY' or proto.state.__name__ == state)}

        for proto in sendto:
            proto.process_packet(p)

    def broadcast_to_all(self, p: packet.Packet, excluding: Iterable[protocol.MoonlapseProtocol] = tuple(), state='ANY'):
        self.broadcast_to(p, including=self.connected_protocols, excluding=excluding, state=state)

    def broadcast_to_room(self, p: packet.Packet, roomid: int,
                          excluding: Iterable[protocol.MoonlapseProtocol] = tuple(), state='ANY'):
        self.broadcast_to(p, including=self.protocols_in_room(roomid), excluding=excluding, state=state)

    def buildProtocol(self, addr):
        print("Adding a new client.")
        return protocol.MoonlapseProtocol(self)

    def is_logged_in(self, pid: int) -> bool:
        for proto in self.connected_protocols:
            if proto.logged_in and proto.player_info:
                if pid == proto.player_info.pk:
                    return True
        return False

    def change_weather(self, new_weather: str):
        print(f"Weather changed from {self.weather} to {new_weather}")

        self.broadcast_to_all(packet.WeatherChangePacket(new_weather), state='PLAY')
        self.weather = new_weather

        if self.weather == "Rain":
            self.broadcast_to_all(packet.ServerLogPacket("It has begun to rain..."), state='PLAY')

        elif self.weather == "Clear":
            self.broadcast_to_all(packet.ServerLogPacket("The rain has cleared."), state='PLAY')

    def rain_check(self):
        # random check here

        if self.weather == "Clear":
            self.change_weather("Rain")

        elif self.weather == "Rain":
            self.change_weather("Clear")

    def save_all_instances(self):
        for key, instance in self.instances.items():
            if instance.entity.typename == 'Player':
                instance.save()
        print("Saved all player instances to DB")
        self.broadcast_to_all(packet.ServerLogPacket("Game has been saved."), state='PLAY')

    def respawn_instance(self, instanceid: int):
        dbi = models.InstancedEntity.objects.get(pk=instanceid)
        self.instances[instanceid].y = dbi.y
        instance = self.instances[instanceid]

        for proto in self.protocols_in_room(instance.room.pk):
            if proto.coord_in_view(instance.y, instance.x):
                proto.process_visible_instances()

import json
import os

import rsa
from Crypto.Cipher import AES
from twisted.internet import task
from twisted.internet.protocol import Factory
from typing import *

from server import manage, models
import server.protocol as protocol
from networking import packet
import maps


class Deferred:
    def __init__(self, f: callable, ticks: int, total_ticks: int, loops: bool, *args):
        """
        This should not be created directly. It should only be created with server.add_deferred()
        :param f: function to fire
        :param ticks: how many ticks until fired
        :param total_ticks: the server's current total ticks
        :param loops: if this deferred loops
        """
        self._f = f
        self.args = args
        self.ticks = ticks
        self.expected_tick = total_ticks + ticks
        self.loops = loops

    def fire(self):
        self._f(*self.args)


class MoonlapseServer(Factory):
    def __init__(self):
        # all protocols connected to server
        self.connected_protocols: Set[protocol.MoonlapseProtocol] = set()

        # dict of all instances in the game. instance.pk : instance
        self.instances: Dict[int, models.InstancedEntity] = {}
        for instance in models.InstancedEntity.objects.all():
            self.instances[instance.pk] = instance

        # set up game tick
        self.tickrate = 20      # hertz (ticks per second)
        tickloop = task.LoopingCall(self.tick)
        tickloop.start(1/self.tickrate, False)
        self.total_ticks = 0

        self.deferreds: List[Deferred] = []

        self.weather = 'Clear'
        # weather change check
        self.add_deferred(self.rain_check, 10*self.tickrate, True)

        # save all instances to DB after loop
        # todo: 20s for testing; obvs should be less often
        self.add_deferred(self.save_all_instances, 20*self.tickrate, True)

        # get encryption keys for sending
        serverdir = os.path.dirname(os.path.realpath(__file__))
        try:
            with open(os.path.join(serverdir, "rsa_keys.json"), 'r') as f:
                d = json.load(f)
                self.public_key = rsa.key.PublicKey(d['PublicKey']['n'], d['PublicKey']['e'])
                self.private_key = rsa.key.PrivateKey(d['PrivateKey']['n'], d['PrivateKey']['e'], d['PrivateKey']['d'],
                                                      d['PrivateKey']['p'], d['PrivateKey']['q'])
        except FileNotFoundError:
            raise FileNotFoundError("RSA keys not configured on the server. Did you set up rsa_keys.json?")
        except json.JSONDecodeError:
            raise KeyError("RSA keys not properly configured on the server. Check the rsa_keys.json file.")

    def tick(self):
        """
        Where all updates happen. Tick rate is how many updates per second.
        """
        for deferred in list(self.deferreds):
            if deferred.expected_tick == self.total_ticks:
                deferred.fire()
                if deferred.loops:
                    deferred.expected_tick = self.total_ticks + deferred.ticks
                else:
                    self.remove_deferred(deferred)

        for proto in self.connected_protocols:
            proto.tick()

        self.total_ticks += 1

    def add_deferred(self, f: callable, ticks: int, loops: bool, *args) -> Deferred:
        """
        @param f the function to be fired
        @param ticks how many ticks in the future until f is fired
        @param loops if this deferred loops
        """
        d = Deferred(f, ticks, self.total_ticks, loops, *args)
        self.deferreds.append(d)
        return d

    def remove_deferred(self, d: Deferred):
        self.deferreds.remove(d)

    def decrypt_string(self, string: bytes):
        # first 64 bytes is the RSA encrypted AES key; remainder is AES encrypted message
        encrypted_key = string[:64]
        encrypted_message = string[64:]

        IV = b'1111111111111111'

        key = rsa.decrypt(encrypted_key, self.private_key)
        cipher = AES.new(key, AES.MODE_CFB, IV=IV)
        message = cipher.decrypt(encrypted_message)
        return message

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

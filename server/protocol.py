import json
import os

import rsa
from Crypto.Cipher import AES
from django.core.exceptions import ObjectDoesNotExist
from django.forms import model_to_dict
from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import NetstringReceiver

from typing import *

from networking import packet
from networking.logger import Log
from server import models, pbkdf2
import maps


def get_dict_delta(before: dict, after: dict) -> dict:
    delta = {'id': before['id']}
    for k, v in after.items():
        if k == 'id':
            continue
        if v != before[k]:
            delta[k] = v

    return delta


def create_dict(model_type: str, model) -> dict:
    """
    Creates recursive dict to replace model_to_dict
    :param model_type: one of ('Instance', 'ContainerItem')
    :param model: a django.model
    :return:
    """
    if model_type == 'Instance':
        instancedict = model_to_dict(model)
        entdict = model_to_dict(model.entity)
        instancedict["entity"] = entdict
        return instancedict

    elif model_type == 'ContainerItem':
        cidict = model_to_dict(model)
        itemdict = model_to_dict(model.item)
        entdict = model_to_dict(model.item.entity)
        cidict["item"] = itemdict
        cidict["item"]["entity"] = entdict
        return cidict


class MoonlapseProtocol(NetstringReceiver):
    def __init__(self, server):
        self.server = server

        # Information specific to the player using this protocol
        self.username = ""
        self.player_instance: Optional[models.InstancedEntity] = None
        self.player_info: Optional[models.Player] = None
        self.roommap: Optional[maps.Room] = None
        self.logged_in = False

        self.state = self.GET_ENTRY

        self.logger = Log()

        self.visible_instances: Set[models.InstancedEntity] = set()

        serverdir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(serverdir, "rsa_keys.json"), 'r') as f:
            d = json.load(f)
            self.public_key = rsa.key.PublicKey(d['PublicKey']['n'], d['PublicKey']['e'])
            self.private_key = rsa.key.PrivateKey(d['PrivateKey']['n'], d['PrivateKey']['e'], d['PrivateKey']['d'],
                                                  d['PrivateKey']['p'], d['PrivateKey']['q'])

    def connectionMade(self):
        self.server.connected_protocols.add(self)
        self.send_packet(packet.ClientKeyPacket(self.public_key.n, self.public_key.e))

    def connectionLost(self, reason=connectionDone):
        self.logout(packet.LogoutPacket(self.username))
        self.server.connected_protocols.remove(self)

    def decrypt_string(self, string: bytes):
        # first 64 bytes is the RSA encrypted AES key; remainder is AES encrypted message
        encrypted_key = string[:64]
        encrypted_message = string[64:]

        IV = b'1111111111111111'

        key = rsa.decrypt(encrypted_key, self.private_key)
        cipher = AES.new(key, AES.MODE_CFB, IV=IV)
        message = cipher.decrypt(encrypted_message)
        return message

    def stringReceived(self, string):
        # attempt to decrypt packet
        string = self.decrypt_string(string)

        p: packet.Packet = packet.frombytes(string)
        self.debug(f"Received packet from my client {p}")
        self.process_packet(p)

    def process_packet(self, p: packet.Packet):
        self.state(p)

    def GET_ENTRY(self, p: packet.Packet):
        if isinstance(p, packet.LoginPacket):
            self.login_user(p)
        elif isinstance(p, packet.RegisterPacket):
            self.register_user(p)

    def login_user(self, p: packet.LoginPacket):
        username, password = p.payloads[0].value, p.payloads[1].value
        if not models.User.objects.filter(username=username):
            self.send_packet(packet.DenyPacket("I don't know anybody by that name"))
            return

        user = models.User.objects.get(username=username)
        player = models.Player.objects.get(user=user)

        if self.server.is_logged_in(player.pk):
            self.send_packet(packet.DenyPacket(f"{username} is already inhabiting this realm."))
            return

        if not pbkdf2.verify_password(user.password, password):
            self.send_packet(packet.DenyPacket("Incorrect password"))
            return

        # The user exists in the database so retrieve the player and entity objects
        self.username = user.username
        self.player_info = player
        self.player_instance = models.InstancedEntity.objects.get(entity=self.player_info.entity)

        self.send_packet(packet.OkPacket())
        self.move_rooms(self.player_instance.room.id)

    def register_user(self, p: packet.RegisterPacket):
        username, password = p.payloads[0].value, p.payloads[1].value

        if models.User.objects.filter(username=username):
            self.send_packet(packet.DenyPacket("Somebody else already goes by that name"))
            return

        password = pbkdf2.hash_password(password)

        # Save the new user
        user = models.User(username=username, password=password)
        user.save()

        # Create and save a new entity
        entity = models.Entity(typename='Player', name=username)
        entity.save()

        # Create and save a new instance
        initial_room = models.Room.objects.first()
        if not initial_room:
            raise ObjectDoesNotExist("Initial room not loaded. Did you run manage.py loaddata data.json?")
        instance = models.InstancedEntity(entity=entity, room=initial_room, y=0, x=0)
        instance.save()

        # Create and save a new container (inventory)
        container = models.Container()
        container.save()

        # Create and save a new player
        player = models.Player(user=user, entity=entity, inventory=container)
        player.save()

        self.send_packet(packet.OkPacket())

    def logout(self, p: packet.LogoutPacket):
        username = p.payloads[0].value
        if username == self.username:
            # Tell our client it's OK to log out
            self.send_packet(packet.OkPacket())

            # tell everyone we're leaving
            if self.player_instance:
                self.broadcast(packet.GoodbyePacket(self.player_instance.pk))

            self.logged_in = False
            self.player_instance = None
            self.player_info = None
            self.roommap = None
            self.username = ""
            self.visible_instances = set()
            self.state = self.GET_ENTRY

    def PLAY(self, p: packet.Packet):
        if isinstance(p, packet.MovePacket):
            self.move(p)
        elif isinstance(p, packet.ChatPacket):
            self.chat(p)
        elif isinstance(p, packet.LogoutPacket):
            self.logout(p)
        elif isinstance(p, packet.GoodbyePacket):
            self.depart_other(p)
        elif isinstance(p, packet.ServerLogPacket):
            self.send_packet(p)
        elif isinstance(p, packet.MoveRoomsPacket):
            self.move_rooms(p.payloads[0].value)
        elif isinstance(p, packet.GrabItemPacket):
            self.grab_item_here()
        elif isinstance(p, packet.WeatherChangePacket):
            self.send_packet(p)

    def chat(self, p: packet.ChatPacket):
        """
        Broadcasts a chat message which includes this protocol's connected player name.
        Truncates to 80 characters. Cannot be empty.
        """
        message: str = p.payloads[0].value
        if message.strip() != '':
            message: str = f"{self.player_instance.entity.name} says: {message[:80]}"
            self.broadcast(packet.ServerLogPacket(message), include_self=True)
            self.logger.log(message)

    def grab_item_here(self):
        # Check if we're standing on an item
        for i in self.visible_instances:
            if i.entity.typename == "Item" and i.y == self.player_instance.y and i.x == self.player_instance.x:
                # remove instanced item from visible instances
                self.broadcast(packet.GoodbyePacket(i.pk), include_self=True)

                # remove instanced item from database
                dbi = models.InstancedEntity.objects.get(pk=i.pk)
                dbi.delete()

                # create ContainerItem from item and add to player.inventory
                itm = models.Item.objects.get(entity_id=dbi.entity_id)
                ci = models.ContainerItem.objects.filter(item=itm, container=self.player_info.inventory).first()
                if ci:
                    ci.amount += i.amount
                    ci.save()
                else:
                    ci = models.ContainerItem(item=itm, amount=i.amount, container=self.player_info.inventory)
                    ci.save()

                # send client ContainerItem packet
                self.send_packet(packet.ServerModelPacket('ContainerItem', create_dict('ContainerItem', ci)))
                return
        self.send_packet(packet.DenyPacket("There is no item here."))

    def depart_other(self, p: packet.GoodbyePacket):
        other_instanceid: int = p.payloads[0].value
        other_instance: models.InstancedEntity = models.InstancedEntity.objects.get(id=other_instanceid)

        if other_instance in self.visible_instances:
            self.visible_instances.remove(other_instance)

        if other_instance.entity.typename == 'Player':
            self.send_packet(packet.ServerLogPacket(f"{other_instance.entity.name} has departed."))
            self.send_packet(p)

    def move(self, p: packet.MovePacket):
        """
        Updates this protocol's player's position and sends the player back to all
        clients connected to the server.
        """

        # Calculate the desired destination
        desired_y = self.player_instance.y
        desired_x = self.player_instance.x

        if isinstance(p, packet.MoveUpPacket):
            desired_y -= 1
        elif isinstance(p, packet.MoveRightPacket):
            desired_x += 1
        elif isinstance(p, packet.MoveDownPacket):
            desired_y += 1
        elif isinstance(p, packet.MoveLeftPacket):
            desired_x -= 1

        # Check if we're going to land on a portal
        for instance in self.visible_instances:
            if instance.entity.typename == "Portal" and instance.y == desired_y and instance.x == desired_x:
                portal: models.Portal = models.Portal.objects.get(entity=instance.entity)
                desired_y = portal.linkedy
                desired_x = portal.linkedx
                self.player_instance.y = desired_y
                self.player_instance.x = desired_x
                self.player_instance.save()
                if self.player_instance.room != portal.linkedroom:
                    self.move_rooms(portal.linkedroom.id)
                    return

        if (0 <= desired_y < self.roommap.height and 0 <= desired_x < self.roommap.width) and (self.roommap.at('solid', desired_y, desired_x) == maps.NOTHING):
            self.player_instance.y = desired_y
            self.player_instance.x = desired_x
            self.player_instance.save()

            for proto in self.server.protocols_in_room(self.player_instance.room_id):
                proto.process_visible_instances()
        else:
            self.send_packet(packet.DenyPacket("Can't move there"))

    def move_rooms(self, dest_roomid: Optional[int]):
        print(f"\nmove_rooms(dest_roomid={dest_roomid})\n")

        if self.logged_in:
            # Tell people in the current (old) room we are leaving
            self.broadcast(packet.GoodbyePacket(self.player_instance.pk))

            # Reset visible entities (so things don't "follow" us between rooms)
            self.visible_instances = set()

        self.logged_in = True

        # Tell our client we're ready to switch rooms so it can reinitialise itself and wait for data again.
        self.send_packet(packet.MoveRoomsPacket(dest_roomid))

        # Move db instance to the new room
        self.player_instance.room_id = dest_roomid
        self.player_instance.save()

        room = self.player_instance.room
        self.roommap = maps.Room(room.pk, room.name, room.file_name)

        self.send_packet(packet.OkPacket())
        self.establish_player_in_room()

    def establish_player_in_room(self):
        self.send_packet(packet.ServerModelPacket('Room', model_to_dict(self.player_instance.room)))
        self.send_packet(packet.ServerModelPacket('Instance', create_dict('Instance', self.player_instance)))

        playerdict = model_to_dict(self.player_info)
        playerdict["entity"] = model_to_dict(self.player_info.entity)
        self.send_packet(packet.ServerModelPacket('Player', playerdict))

        self.send_packet(packet.WeatherChangePacket(self.server.weather))

        # send inventory to player
        items = models.ContainerItem.objects.filter(container=self.player_info.inventory)
        for ci in items:
            self.send_packet(packet.ServerModelPacket('ContainerItem', create_dict('ContainerItem', ci)))

        self.state = self.PLAY
        self.broadcast(packet.ServerLogPacket(f"{self.username} has arrived."))

        # Tell other players in view that we have arrived
        for proto in self.server.protocols_in_room(self.player_instance.room_id):
            proto.process_visible_instances()

    def process_visible_instances(self):
        """
        Say goodbye to old entities no longer in view and process the new and still-existing entities in view
        """
        yview = self.player_instance.y - 10, self.player_instance.y + 10
        xview = self.player_instance.x - 10, self.player_instance.x + 10

        prev_in_view = self.visible_instances

        instances_in_view = set(models.InstancedEntity.objects.filter(room=self.player_instance.room, y__gte=yview[0],
                                                                      y__lte=yview[1], x__gte=xview[0],
                                                                      x__lte=xview[1]))
        # removing logged out players from view
        for instance in set(instances_in_view):
            if instance == self.player_instance:
                continue

            if instance.entity.typename == 'Player':
                proto = self.server.get_proto_by_id(instance.entity.pk)
                if not proto or not proto.logged_in:
                    instances_in_view.remove(instance)

        self.visible_instances = instances_in_view

        # just left view
        for instance in prev_in_view:
            if instance not in self.visible_instances:
                self.send_packet(packet.GoodbyePacket(instance.pk))

        for instance in self.visible_instances:
            # new to view
            if instance not in prev_in_view:
                self.send_packet(packet.ServerModelPacket('Instance', create_dict('Instance', instance)))
                continue

            # dict delta for those still in view
            after = instance
            for before in prev_in_view:
                if before.pk == after.pk:
                    delta = get_dict_delta(create_dict('Instance', before), create_dict('Instance', after))
                    self.send_packet(packet.ServerModelPacket('Instance', delta))

    def send_packet(self, p: packet.Packet):
        """
        Sends a packet to this protocol's client.
        Call this to communicate information back to the game client application.
        """
        self.sendString(p.tobytes())
        self.debug(f"Sent data to my client: {p.tobytes()}")

    def broadcast(self, p: packet.Packet, include_self=False):
        excluding = []
        if not include_self:
            excluding.append(self)
        self.server.broadcast_to_room(p, self.player_instance.room.pk, excluding=excluding)

    def debug(self, message: str):
        print(f"[{self.username if self.username else None}]"
              f"[{self.state.__name__}]"
              f"[{self.player_instance.room.name if self.player_instance else None}]: {message}")

    def coord_in_view(self, y: int, x: int) -> bool:
        yview = self.player_instance.y - 10, self.player_instance.y + 10
        xview = self.player_instance.x - 10, self.player_instance.x + 10

        return yview[0] <= y <= yview[1] and xview[0] <= x <= xview[1]

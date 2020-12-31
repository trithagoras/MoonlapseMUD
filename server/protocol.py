from twisted.protocols.basic import NetstringReceiver
from twisted.python.failure import Failure

from Crypto.Cipher import AES

from server.__main__ import MoonlapseServer
from networking import packet
from networking import models
from networking.logger import Log
import pbkdf2

from typing import *
import time
from django.forms.models import model_to_dict
from django.core.exceptions import ObjectDoesNotExist

import rsa
import json
import os

import maps


def within_bounds(y: int, x: int, ymin: int, xmin: int, ymax: int, xmax: int) -> bool:
    """
    Checks if the given coordinates are inside the square defined by the top left and bottom right corners.
    Includes all values in the square, even right/bottom-most parts.
    """
    return ymin <= y <= ymax and xmin <= x <= xmax


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


class Moonlapse(NetstringReceiver):
    """
    A protocol that sends and receives netstrings. See http://cr.yp.to/proto/netstrings.txt for the 
    specification of netstrings.

    The constructing and sending of netstrings is handled by the networking.packet package, as Moonlapse 
    has its own Packet class which encapsulates packet types and payloads as netstrings for communication 
    between protocols and clients.

    The self.stringReceived method handles received netstrings. This method is called with the netstring 
    payload as a single argument whenever a complete netstring is received. This method should never be 
    called external to the underlying twisted.protocols.basic.NetstringReceiver implementation. It is fired 
    every time data this protocol receives a full netstring's worth of bytes data.

    The self.sendPacket method is used to send a packet back to this protocol's client.

    The self.processPacket method is used to tell another protocol on the server to process a packet which 
    doesn't necessarily have to be sent to any clients.
    """

    def __init__(self, server: MoonlapseServer, others: Set['Moonlapse']):
        super().__init__()

        # Information specific to this protocol
        self._server: MoonlapseServer = server
        self._others: Set['Moonlapse'] = others

        # Information specific to the player using this protocol
        self.username = ""
        self._instance: Optional[models.InstancedEntity] = None
        self._player: Optional[models.Player] = None
        self._room: Optional[models.Room] = None
        self._roommap: Optional[maps.Room] = None
        self._visible_instances: Set[models.InstancedEntity] = set()

        self._logged_in: bool = False

        # The state of the protocol which gets called as a function to process only the packets 
        # intended to be processed in the protocol's current state. Should only be called in the 
        # self.stringReceived method every time a complete netstring is received and converted to 
        # a packet.
        self.state: Callable = self._GETENTRY

        self.logger: Log = Log()

        serverdir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(serverdir, "rsa_keys.json"), 'r') as f:
            d = json.load(f)
            self.public_key = rsa.key.PublicKey(d['PublicKey']['n'], d['PublicKey']['e'])
            self.private_key = rsa.key.PrivateKey(d['PrivateKey']['n'], d['PrivateKey']['e'], d['PrivateKey']['d'],
                                                  d['PrivateKey']['p'], d['PrivateKey']['q'])

    def _debug(self, message: str):
        print(f"[{self.username if self.username else None}]"
              f"[{self.state.__name__}]"
              f"[{self._instance.room.name if self._instance else None}]: {message}")

    def connectionMade(self) -> None:
        super().connectionMade()
        servertime: str = time.strftime('%d %B, %Y %R %p', time.gmtime())
        # self.sendPacket(packet.WelcomePacket(f"Welcome to MoonlapseMUD. Server time is {servertime}"))
        self.sendPacket(packet.ClientKeyPacket(self.public_key.n, self.public_key.e))

    def connectionLost(self, reason: Failure = None) -> None:
        super().connectionLost()
        self.state = self._DISCONNECT
        self.processPacket(packet.DisconnectPacket(self.username, reason))

    def _decrypt_string(self, string: bytes):
        # first 64 bytes is the RSA encrypted AES key; remainder is AES encrypted message
        encrypted_key = string[:64]
        encrypted_message = string[64:]

        IV = b'1111111111111111'

        key = rsa.decrypt(encrypted_key, self.private_key)
        cipher = AES.new(key, AES.MODE_CFB, IV=IV)
        message = cipher.decrypt(encrypted_message)
        return message

    def stringReceived(self, string: bytes) -> None:
        """
        Processes data sent from this protocol's client.
        This should never be called directly. It's handled by NetStringReceiver 
        on dataReceived.
        """
        self._debug(f"Received encrypted data from my client {string}")

        # attempt to decrypt packet
        string = self._decrypt_string(string)

        p: packet.Packet = packet.frombytes(string)
        self._debug(f"Received packet from my client {p}")
        self.state(p)

    def sendPacket(self, p: packet.Packet) -> None:
        """
        Sends a packet to this protocol's client.
        Call this to communicate information back to the game client application.
        """
        self.sendString(p.tobytes())
        self._debug(f"Sent data to my client: {p.tobytes()}")

    def processPacket(self, p: packet.Packet) -> None:
        """
        Processes packets sent to this protocol from another protocol.
        Call this to communicate with other protocols connected to the main server.
        """
        self._debug(f"Received packet from a protocol {p}")
        self.state(p)

    def _PLAY(self, p: packet.Packet) -> None:
        """
        Handles packets received when this protocol is in the PLAY state.
        This should never be called directly and is instead handled by
        stringReceived.
        """
        if isinstance(p, packet.MovePacket):
            self.move(p)
        elif isinstance(p, packet.ChatPacket):
            self.chat(p)
        elif isinstance(p, packet.LogoutPacket):
            self.logout(p)
        elif isinstance(p, packet.GoodbyePacket):
            self.depart_other(p)
        elif isinstance(p, packet.ServerLogPacket):
            self.sendPacket(p)
        elif isinstance(p, packet.MoveRoomsPacket):
            self.move_rooms(p.payloads[0].value)
        elif isinstance(p, packet.ServerModelPacket):
            self.process_model(p)
        elif isinstance(p, packet.GrabItemPacket):
            self.grab_item_here()
        elif isinstance(p, packet.WeatherChangePacket):
            self.sendPacket(p)

    def _GETENTRY(self, p: Union[packet.LoginPacket, packet.RegisterPacket]) -> None:
        """
        Handles packets received when this protocol is in the GETENTRY state.
        This should never be called directly and is instead handled by
        stringReceived.
        """
        if isinstance(p, packet.LoginPacket):
            self._login_user(p.payloads[0].value, p.payloads[1].value)
        elif isinstance(p, packet.RegisterPacket):
            self._register_user(p)

    def _login_user(self, username: str, password: str) -> None:
        if not models.User.objects.filter(username=username):
            self.sendPacket(packet.DenyPacket("I don't know anybody by that name"))
            return

        user = models.User.objects.get(username=username)
        if not pbkdf2.verify_password(user.password, password):
            self.sendPacket(packet.DenyPacket("Incorrect password"))
            return

        # The user exists in the database so retrieve the player and entity objects
        self.username = user.username
        self._player = models.Player.objects.get(user=user)
        self._instance = models.InstancedEntity.objects.get(entity=self._player.entity)

        self.move_rooms(self._instance.room.id)

    def move_rooms(self, dest_roomid: Optional[int]):
        print(f"\nmove_rooms(dest_roomid={dest_roomid})\n")

        # Tell people in the current (old) room we are leaving
        self.broadcast(packet.GoodbyePacket(self._instance.id), excluding=(self,))

        # Reset visible entities (so things don't "follow" us between rooms)
        self._visible_instances = set()

        # If the destination room is None (i.e. we are going to the lobby), skip the rest
        if dest_roomid is None:
            self._room = None
            return

        # Tell our client we're ready to switch rooms so it can reinitialise itself and wait for data again.
        if self._room is not None:
            self.sendPacket(packet.MoveRoomsPacket(dest_roomid))

        # Move to the new room
        self._server.moveProtocols(self, dest_roomid)

        self._instance.room_id = dest_roomid
        self._instance.save()

        self._room = models.Room.objects.get(id=dest_roomid)
        self._roommap = maps.Room(self._room.pk, self._room.name, self._room.file_name)

        self._others = self._server.rooms_protocols[dest_roomid]
        self._establish_player_in_world()

    def _establish_player_in_world(self) -> None:
        print(f"\n_establish_player_in_world()\n")
        self.sendPacket(packet.OkPacket())

        # Assign the starting position if not already done
        if None in (self._instance.y, self._instance.x):
            self._instance.y = 0
            self._instance.x = 0
            self._instance.save()

        # Send new data to the client
        self.sendPacket(packet.ServerTickRatePacket(100))

        roomdict: dict = model_to_dict(self._room)
        self.sendPacket(packet.ServerModelPacket('Room', roomdict))

        self.sendPacket(packet.ServerModelPacket('Instance', create_dict('Instance', self._instance)))

        playerdict: dict = model_to_dict(self._player)
        playerdict["entity"] = model_to_dict(self._player.entity)
        self.sendPacket(packet.ServerModelPacket('Player', playerdict))

        # send weather info to player
        self.sendPacket(packet.WeatherChangePacket(self._server.weather))

        # send inventory to player
        items = models.ContainerItem.objects.filter(container=self._player.inventory)
        for ci in items:
            self.sendPacket(packet.ServerModelPacket('ContainerItem', create_dict('ContainerItem', ci)))

        self.state = self._PLAY
        self.broadcast(packet.ServerLogPacket(f"{self.username} has arrived."), excluding=(self,))
        self._logged_in = True

        # Tell entities in view that we have arrived
        self.broadcast(packet.HelloPacket(create_dict('Instance', self._instance)), excluding=(self,))

        # Tell our client about all the entities around
        self._process_visible_instances()

    def _process_visible_instances(self):
        """
        Say goodbye to old entities no longer in view and process the new and still-existing entities in view
        """
        for instance in list(self._visible_instances):  # Loop through list to avoid changing set size during iteration
            currently_in_view = self._coord_in_view(instance.y, instance.x)
            if not currently_in_view:
                self.sendPacket(packet.GoodbyePacket(instance.id))
                self._visible_instances.remove(instance)

        ybounds, xbounds = self._get_view_bounds()
        for instance in models.InstancedEntity.objects.filter(room=self._room, y__gte=ybounds[0], y__lte=ybounds[1], x__gte=xbounds[0], x__lte=xbounds[1]):
            # TODO: Stop looping through entities that belong to logged out players
            if instance.entity.typename == 'Player':
                other_protocols = {p._instance: p for p in self._others}
                if instance not in other_protocols:
                    continue
                if other_protocols[instance]._room != self._room:
                    continue

            model_packet = packet.ServerModelPacket('Instance', create_dict('Instance', instance))
            self.process_model(model_packet)

    def logout(self, p: packet.LogoutPacket):
        username: str = p.payloads[0].value
        if username == self.username:
            # Tell our client it's OK to log out
            self.sendPacket(packet.OkPacket())
            self.broadcast(packet.GoodbyePacket(self._instance.id), excluding=(self,))
            self.move_rooms(None)
            self._logged_in = False
            self.state = self._GETENTRY

    def depart_other(self, p: packet.GoodbyePacket):
        other_instanceid: int = p.payloads[0].value
        other_instance: models.InstancedEntity = models.InstancedEntity.objects.get(id=other_instanceid)

        if other_instance in self._visible_instances:
            self._visible_instances.remove(other_instance)

        #todo: remove this comment otherwise picking up a beer broadcasts 'Beer has departed.'
        # if other_instance.entity.typename == 'Player':
        self.sendPacket(packet.ServerLogPacket(f"{other_instance.entity.name} has departed."))
        self.sendPacket(p)

    def _register_user(self, p: packet.RegisterPacket) -> None:
        username: str = p.payloads[0].value
        password: str = p.payloads[1].value

        if models.User.objects.filter(username=username):
            self.sendPacket(packet.DenyPacket("Somebody else already goes by that name"))
            return

        password = pbkdf2.hash_password(password)

        # Save the new user
        user = models.User(username=username, password=password)
        user.save()

        # Create and save a new entity
        entity = models.Entity(typename='Player', name=username)
        entity.save()

        # Create and save a new instance
        initial_room: models.Room = models.Room.objects.first()
        if not initial_room:
            raise ObjectDoesNotExist("Initial room not loaded. Did you run manage.py loaddata data.json?")
        instance = models.InstancedEntity(entity=entity, room=initial_room)
        instance.save()

        # Create and save a new container
        container = models.Container()
        container.save()

        # Create and save a new player
        # TODO: Get default room
        player = models.Player(user=user, entity=entity, inventory=container)
        player.save()

        self.sendPacket(packet.OkPacket())

    def greet(self, p: packet.HelloPacket):
        model: dict = p.payloads[0].value

        # We don't greet entities that don't belong to other protocols
        other_proto: Optional['Moonlapse'] = next((p for p in self._others if p._instance.id == model['id']), None)
        if other_proto is None:
            return

        # Broadcasts our entity model to the other player's protocol
        self.broadcast(packet.ServerModelPacket('Instance', create_dict('Instance', self._instance)), including=(other_proto,))

    def process_model(self, p: packet.ServerModelPacket):
        type: str = p.payloads[0].value
        model: dict = p.payloads[1].value
        instanceid: int = model['id']

        # Send the new model to the client if it's still within our view - otherwise remove it from our list of visible
        # entities
        if type == 'Instance':
            currently_in_view = self._coord_in_view(model['y'], model['x'])
            previously_in_view = instanceid in {e.id for e in self._visible_instances}

            if currently_in_view:
                stored_instance = models.InstancedEntity.objects.get(id=model['id'])
                # If it's in our view, and it wasn't PREVIOUSLY in our view, say hello to it
                if not previously_in_view:
                    self._debug("Instance currently in view, and wasn't there before, so greet it")
                    self._visible_instances.add(stored_instance)
                    self.sendPacket(p)
                    self.greet(packet.HelloPacket(model))
                else:
                    # If it was previously in our view and still is, tell our client about it only if it's changed
                    before = model_to_dict(stored_instance)
                    if model != before:
                        delta = get_dict_delta(before, model)
                        self.sendPacket(packet.ServerModelPacket('Instance', delta))
            else:
                # Else, it's not in our view but check if it WAS so we can say goodbye to it
                self._debug(f"Instance not in view, not telling my client about it")
                if previously_in_view:
                    self._debug(f"Actually, it was previously in view but it's not now so I'll tell my client to remove it")
                    self.sendPacket(packet.GoodbyePacket(instanceid))
                    self._remove_visible_instance(instanceid)

    def _remove_visible_instance(self, instanceid: int):
        self._visible_instances = {i for i in self._visible_instances if i.id != instanceid}

    def _DISCONNECT(self, p: packet.DisconnectPacket):
        """
        Handles packets received when this protocol is in the DISCONNECT state.
        Releases this protocol from the server and informs all other protocols
        of this disconnection. No more code should be executed from this protocol.

        This should never be called directly. Instead it should be handled by
        self.connectionLost.
        """
        reason: Optional[Failure] = None
        if len(p.payloads) > 1:
            reason = p.payloads[1].value

        if self._logged_in:
            self.sendPacket(packet.DisconnectPacket(self.username, reason=reason.getErrorMessage()))
            self._logged_in = False

        # Release this protocol from the server
        if self in self._others:
            self._others.remove(self)
            self._debug(f"Deleted self from others list")

        # Tell all still connected protocols about this disconnection
        self.broadcast(packet.GoodbyePacket(self._instance.id))

    def broadcast(self, *packets: packet.Packet, including: Iterable['Moonlapse'] = tuple(), excluding: Iterable['Moonlapse'] = tuple()) -> None:
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
        self._debug(f"Broadcasting {packets} to {tuple(p.username for p in including) if including else 'everyone'} "
                    f"{'except' + str(tuple(p.username for p in excluding)) if tuple(p.username for p in excluding) else ''}")

        sendto: Set['Moonlapse'] = self._others
        if including:
            sendto = including

        sendto = {proto for proto in sendto if proto not in excluding}

        for proto in sendto:
            for p in packets:
                proto.processPacket(p)

    def chat(self, p: packet.ChatPacket) -> None:
        """
        Broadcasts a chat message which includes this protocol's connected player name.
        Truncates to 80 characters. Cannot be empty.
        """
        message: str = p.payloads[0].value
        if message.strip() != '':
            message: str = f"{self._instance.entity.name} says: {message[:80]}"
            self.broadcast(packet.ServerLogPacket(message))
            self.logger.log(message)

    def move(self, p: packet.MovePacket) -> None:
        """
        Updates this protocol's player's position and sends the player back to all 
        clients connected to the server.

        NOTE: This method should be avoided in a future release to prevent sending more
              information than is required. A client will know all the information 
              about every player connected to the server even if they are not in view.
        """

        # Calculate the desired destination
        desired_y: int = self._instance.y
        desired_x: int = self._instance.x

        if isinstance(p, packet.MoveUpPacket):
            desired_y -= 1
        elif isinstance(p, packet.MoveRightPacket):
            desired_x += 1
        elif isinstance(p, packet.MoveDownPacket):
            desired_y += 1
        elif isinstance(p, packet.MoveLeftPacket):
            desired_x -= 1

        # Check if we're going to land on a portal
        for e in self._visible_instances:
            if e.entity.typename == "Portal" and e.y == desired_y and e.x == desired_x:
                portal: models.Portal = models.Portal.objects.get(entity=e.entity)
                desired_y = portal.linkedy
                desired_x = portal.linkedx
                if self._room != portal.linkedroom:
                    self.move_rooms(portal.linkedroom.id)

        if not within_bounds(desired_y, desired_x, 0, 0, self._roommap.height - 1, self._roommap.width - 1) or self._roommap.at('solid', desired_y, desired_x) != maps.NOTHING:
            self.sendPacket(packet.DenyPacket("Can't move there"))
            return

        self._instance.y = desired_y
        self._instance.x = desired_x

        # Broadcast our new position to other protocols in the room
        self.broadcast(packet.ServerModelPacket('Instance', create_dict('Instance', self._instance)))
        # Process the entities around us
        self._process_visible_instances()

        self._instance.save()

    def _coord_in_view(self, y: int, x: int) -> bool:
        ybounds, xbounds = self._get_view_bounds()
        return within_bounds(y, x, ybounds[0], xbounds[0], ybounds[1], xbounds[1])

    def _get_view_bounds(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Returns two tuples: ((ymin, ymax), (xmin, xmax)) where ymin is the smallest y-coordinate the player can see, etc.
        :return:
        """
        yview = self._instance.y - 10, self._instance.y + 10
        xview = self._instance.x - 10, self._instance.x + 10
        return yview, xview

    def grab_item_here(self):
        # Check if we're standing on an item
        for i in self._visible_instances:
            if i.entity.typename == "Item" and i.y == self._instance.y and i.x == self._instance.x:
                # remove instanced item from visible instances
                self.broadcast(packet.GoodbyePacket(i.pk))
                # remove instanced item from database
                dbi = models.InstancedEntity.objects.get(pk=i.pk)
                dbi.delete()
                # create ContainerItem from item and add to player.inventory
                itm = models.Item.objects.get(entity_id=dbi.entity_id)
                ci = models.ContainerItem.objects.filter(item=itm).first()
                if ci:
                    ci.amount += i.amount
                    ci.save()
                else:
                    ci = models.ContainerItem(item=itm, amount=i.amount, container=self._player.inventory)
                    ci.save()
                # send client ContainerItem packet
                self.sendPacket(packet.ServerModelPacket('ContainerItem', create_dict('ContainerItem', ci)))
                return




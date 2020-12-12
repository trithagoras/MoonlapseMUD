from twisted.protocols.basic import NetstringReceiver
from twisted.python.failure import Failure

from server.__main__ import MoonlapseServer
import manage
from networking import packet
from networking import models
from networking.logger import Log

from typing import *
import time
from django.forms.models import model_to_dict

import maps


def within_bounds(y: int, x: int, ymin: int, xmin: int, ymax: int, xmax: int) -> bool:
    """
    Checks if the given coordinates are inside the square defined by the top left and bottom right corners.
    Includes all values in the square, even right/bottom-most parts.
    """
    return ymin <= y <= ymax and xmin <= x <= xmax


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
    def __init__(self, server: MoonlapseServer, roomid: Optional[int], others: Set['Moonlapse']):
        super().__init__()

        # Information specific to this protocol
        self._server: MoonlapseServer = server
        self._others: Set['Moonlapse'] = others

        # Information specific to the player using this protocol
        self._user: Optional[models.User] = None
        self._entity: Optional[models.Entity] = None
        self._player: Optional[models.Player] = None
        self._room: Optional[models.Room] = None
        self._roommap: Optional[maps.Room] = None
        self._visible_entities: Set[models.Entity] = set()

        self._logged_in: bool = False

        # The state of the protocol which gets called as a function to process only the packets 
        # intended to be processed in the protocol's current state. Should only be called in the 
        # self.stringReceived method every time a complete netstring is received and converted to 
        # a packet.
        self.state: Callable = self._GETENTRY

        self.logger: Log = Log()

    def _debug(self, message: str):
        print(f"[{self._user.username if self._user else None }]"
              f"[{self.state.__name__}]"
              f"[{self._entity.room.name if self._entity else None}]: {message}")

    def connectionMade(self) -> None:
        super().connectionMade()
        servertime: str = time.strftime('%d %B, %Y %R %p', time.gmtime())
        self.sendPacket(packet.WelcomePacket(f"Welcome to MoonlapseMUD. Server time is {servertime}"))

    def connectionLost(self, reason: Failure = None) -> None:
        super().connectionLost()
        self.state = self._DISCONNECT
        self.processPacket(packet.DisconnectPacket(self._user.username, reason))

    def stringReceived(self, string: bytes) -> None:
        """
        Processes data sent from this protocol's client.
        This should never be called directly. It's handled by NetStringReceiver 
        on dataReceived.
        """
        p: packet.Packet = packet.frombytes(string)
        self._debug(f"Received packet from my client {p}")
        self.state(p)

    def sendPacket(self, p: packet.Packet) -> None:
        """
        Sends a packet to this protocol's client.
        Call this to communicate information back to the game client application.
        """
        self.transport.write(p.tobytes())
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
        elif isinstance(p, packet.HelloPacket):
            self.greet(p)

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

        if not models.User.objects.filter(username=username, password=password):
            self.sendPacket(packet.DenyPacket("Incorrect password"))
            return

        # The user exists in the database so retrieve the player and entity objects
        self._user = models.User.objects.get(username=username)
        self._player = models.Player.objects.get(user=self._user.id)
        self._entity = models.Entity.objects.get(id=self._player.entity.id)

        self.move_rooms(self._entity.room.id)

    def move_rooms(self, dest_roomid: Optional[int]):
        print(f"\nmove_rooms(dest_roomid={dest_roomid})\n")

        # Tell people in the current (old) room we are leaving
        self.broadcast(packet.GoodbyePacket(self._entity.id), excluding=(self._user.username,))

        # If the destination room is None (i.e. we are going to the lobby), skip the rest
        if dest_roomid is None:
            return

        # Move to the new room
        self._server.moveProtocols(self, dest_roomid)

        self._entity.room_id = dest_roomid
        self._entity.save()

        self._room = models.Room.objects.get(id=dest_roomid)
        self._roommap = maps.Room(self._room.name)
        if not self._roommap.is_unpacked():
            self._roommap.unpack()

        self._others = self._server.rooms_protocols[dest_roomid]
        self._establish_player_in_world()

    def _establish_player_in_world(self) -> None:
        print(f"\n_establish_player_in_world()\n")
        self.sendPacket(packet.OkPacket())

        # Assign the starting position if not already done
        if None in (self._entity.y, self._entity.x):
            self._entity.y = 0
            self._entity.x = 0
            self._entity.save()

        # Send new data to the client
        self.sendPacket(packet.ServerTickRatePacket(100))

        userdict: dict = model_to_dict(self._user)
        self.sendPacket(packet.ServerModelPacket('User', userdict))

        roomdict: dict = model_to_dict(self._room)
        self.sendPacket(packet.ServerModelPacket('Room', roomdict))

        entitydict: dict = model_to_dict(self._entity)
        self.sendPacket(packet.ServerModelPacket('Entity', entitydict))

        playerdict: dict = model_to_dict(self._player)
        self.sendPacket(packet.ServerModelPacket('Player', playerdict))

        self.state = self._PLAY
        self.broadcast(packet.ServerLogPacket(f"{self._user.username} has arrived."))
        self._logged_in = True

        # Reset visible entities (so things don't "follow" us between rooms)
        self._visible_entities = set()

        # Tell entities in view that we have arrived
        self.broadcast(packet.HelloPacket(model_to_dict(self._entity)), excluding=(self._user.username,))

        # Tell our client about all the entities around
        self._process_entities()

    def _process_entities(self):
        for entity in models.Entity.objects.filter(room=self._room):
            # TODO: Don't loop through all players
            if entity.id in (p.entity.id for p in models.Player.objects.all()):
                # Don't send players as that's done separately
                continue
            model_packet = packet.ServerModelPacket('Entity', model_to_dict(entity))
            self.process_model(model_packet)

    def logout(self, p: packet.LogoutPacket):
        username: str = p.payloads[0].value
        if username == self._user.username:
            # Tell our client it's OK to log out
            self.sendPacket(packet.OkPacket())
            self.broadcast(packet.GoodbyePacket(self._entity.id), excluding=(self._user.username,))
            self.move_rooms(None)
            self._logged_in = False
            self.state = self._GETENTRY

    def depart_other(self, p: packet.GoodbyePacket):
        other_entityid: int = p.payloads[0].value
        other_entity: models.Entity = models.Entity.objects.get(id=other_entityid)

        if other_entity in self._visible_entities:
            self._visible_entities.remove(other_entity)
        self.sendPacket(packet.ServerLogPacket(f"{other_entity.name} has departed."))
        self.sendPacket(p)

    def _register_user(self, p: packet.RegisterPacket) -> None:
        username: str = p.payloads[0].value
        password: str = p.payloads[1].value
        char: chr = p.payloads[2].value

        if models.User.objects.filter(username=username):
            self.sendPacket(packet.DenyPacket("Somebody else already goes by that name"))
            return

        # Save the new user
        user = models.User(username=username, password=password)
        user.save()

        # Create and save a new entity
        entity = models.Entity(room=models.Room.objects.first(), typename='Player', name=username, char=char)
        entity.save()

        # Create and save a new player
        # TODO: Get default room
        player = models.Player(user=user, entity=entity)
        player.save()

        self.sendPacket(packet.OkPacket())

    # Interaction plan
    # Cases:
    # 1. * Player A already in room
    #    * Player B joins room and broadcasts its entity model to every protocol in the room
    #    * Player A's protocol checks if Player B's entity is within view; if so:
    #          * Player A tells its client about Player B
    #    * Player A broadcasts its entity model to Player B's protocol
    #    * Player B's protocol checks if Player A's entity is within view; if so:
    #          * Player B tells its client about Player A
    def greet(self, p: packet.HelloPacket):
        model: dict = p.payloads[0].value
        # Obtain Player B's protocol
        other_proto: Optional['Moonlapse'] = next((p for p in self._others if p._entity.id == model['id']), None)
        if other_proto is None:
            return

        # Player A's protocol checks if Player B's entity is within view; if so:
        if self.coord_in_view(other_proto._entity.y, other_proto._entity.x):
            self._visible_entities.add(other_proto._entity)
            # Player A tells its client about Player B
            self.sendPacket(packet.ServerModelPacket('Entity', model))
        else:
            self._debug(f"{other_proto._entity.name} not in my view so I won't tell my client about it")

        # Player A broadcasts its entity model to Player B's protocol
        other_proto.processPacket(packet.ServerModelPacket('Entity', model_to_dict(self._entity)))

        # Now the rest of the logic is passed to proto.process_model

    def process_model(self, p: packet.ServerModelPacket):
        type: str = p.payloads[0].value
        model: dict = p.payloads[1].value

        # Send the new model to the client if it's still within our view - otherwise remove it from our list of visible
        # entities
        if type == 'Entity':
            if self.coord_in_view(model['y'], model['x']):
                # If it's in our view, tell our client about it
                self.sendPacket(p)
                model_room = models.Room.objects.get(id=model['room'])
                entity = models.Entity(id=model['id'], room=model_room, y=model['y'], x=model['x'], char=model['char'], typename=model['typename'], name=model['name'])
                self._debug(f"Entity {entity.name} in view, adding to visible entities")
                self._visible_entities.add(entity)
            else:
                # Else, it's not in our view but check if it WAS so we can say goodbye to it
                entityid: int = model['id']
                self.sendPacket(packet.GoodbyePacket(entityid))
                self._remove_visible_entity(entityid)

    def _remove_visible_entity(self, entityid: int):
        self._visible_entities = {e for e in self._visible_entities if e.id != entityid}

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
            self.sendPacket(packet.DisconnectPacket(self._user.username, reason=reason.getErrorMessage()))
            self._logged_in = False

        # Release this protocol from the server
        if self in self._others:
            self._others.remove(self)
            self._debug(f"Deleted self from others list")

        # Tell all still connected protocols about this disconnection
        for proto in self._others:
            proto.processPacket(packet.GoodbyePacket(self._entity.id))

    def broadcast(self, *packets: packet.Packet, including: Iterable[str] = tuple(), excluding: Iterable[str] = tuple()) -> None:
        """
        Sends packets to all protocols specified in "including" except for the ones for the usernames specified in
        "excluding", if any.
        If no protocols are specified in "including", the default behaviour is to send to *all* protocols on the server
        except for the ones specified in "excluding", if any.

        Examples:
            * broadcast(packet.ServerLogPacket("Hello"), excluding=("Josh",)) will send to everyone but Josh
            * broadcast(packet.ServerLogPacket("Hello"), including=("Sue", "James")) will send to only Sue and James
            * broadcast(packet.ServerLogPacket("Hello"), including=("Mary",), excluding=("Mary",)) will send to noone
        """
        self._debug(f"Broadcasting {packets} to {including if including else 'everyone'} except {excluding}")

        sendto: Set['Moonlapse'] = self._others
        if including:
            sendto = {proto for proto in self._others if proto._user.username in including}

        sendto = {proto for proto in sendto if proto._user.username not in excluding}

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
            message: str = f"{self._entity.name} says: {message[:80]}"
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
        desired_y: int = self._entity.y
        desired_x: int = self._entity.x

        if isinstance(p, packet.MoveUpPacket):
            desired_y -= 1
        elif isinstance(p, packet.MoveRightPacket):
            desired_x += 1
        elif isinstance(p, packet.MoveDownPacket):
            desired_y += 1
        elif isinstance(p, packet.MoveLeftPacket):
            desired_x -= 1

        # Check if we're going to land on a portal
        for e in self._visible_entities:
            if e.typename == "Portal" and e.y == desired_y and e.x == desired_x:
                portal: models.Portal = models.Portal.objects.get(entity=e)
                desired_y = portal.linkedy
                desired_x = portal.linkedx

        if (desired_y, desired_x) in self._roommap.solidmap or not within_bounds(desired_y, desired_x, 0, 0, self._room.height - 1, self._room.width - 1):
            self.sendPacket(packet.DenyPacket("Can't move there"))
            return

        self._entity.y = desired_y
        self._entity.x = desired_x
        self._entity.save()

        # Broadcast our new position to other protocols in the room
        self.broadcast(packet.ServerModelPacket('Entity', model_to_dict(self._entity)))
        # Send greetings to keep the views up to date
        self.broadcast(packet.HelloPacket(model_to_dict(self._entity)))
        # Process the entities around us
        self._process_entities()

        # For players which were previously in our view but aren't any more, remove them from our view
        for old_entity_in_view in tuple(self._visible_entities):    # Iterate over tuple to void "Set changed size during iteration" errors
            if not self.coord_in_view(old_entity_in_view.y, old_entity_in_view.x):
                self._visible_entities.remove(old_entity_in_view)

    def coord_in_view(self, y: int, x: int) -> bool:
        topleft_y, topleft_x = self._entity.y - self._player.view_radius, self._entity.x - self._player.view_radius
        botright_y, botright_x = self._entity.y + self._player.view_radius, self._entity.x + self._player.view_radius
        return within_bounds(y, x, topleft_y, topleft_x, botright_y, botright_x)

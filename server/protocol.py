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
        self._roomid: Optional[int] = roomid
        self._others: Set['Moonlapse'] = others

        # Information specific to the player using this protocol
        self._user: Optional[models.User] = None
        self._entity: Optional[models.Entity] = None
        self._player: Optional[models.Player] = None
        self._room: Optional[models.Room] = None
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
              f"[{self._entity.room.id if self._entity else None}]: {message}")

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

    def _GETENTRY(self, p: Union[packet.LoginPacket, packet.RegisterPacket]) -> None:
        """
        Handles packets received when this protocol is in the GETENTRY state.
        This should never be called directly and is instead handled by
        stringReceived.
        """
        if isinstance(p, packet.LoginPacket):
            self._login_user(p.payloads[0].value, p.payloads[1].value)
        elif isinstance(p, packet.RegisterPacket):
            self._register_user(p.payloads[0].value, p.payloads[1].value)

    def _login_user(self, username: str, password: str) -> None:
        if username in [proto.user.username for proto in self._others]:
            self.sendPacket(packet.DenyPacket("You are already inhabiting this realm"))
            self.sendPacket(packet.DenyPacket("You are already inhabiting this realm"))
            return

        if not models.User.objects.filter(username=username):
            self.sendPacket(packet.DenyPacket("I don't know anybody by that name"))
            return

        if not models.User.objects.filter(password=password):
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

        # Move to the new room
        self._server.moveProtocols(self, dest_roomid)

        self._entity.room.id = dest_roomid
        self._entity.save()

        self._room = maps.Room(models.Room.objects.get(id=dest_roomid).name)

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

    def logout(self, p: packet.LogoutPacket):
        username: str = p.payloads[0].value
        if username == self._user.username:
            # Tell our client it's OK to log out
            self.sendPacket(packet.OkPacket())
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

    def _register_user(self, username: str, password: str) -> None:
        if models.User.objects.filter(username=username):
            self.sendPacket(packet.DenyPacket("Somebody else already goes by that name"))
            return

        # Save the new user
        user = models.User(username=username, password=password)
        user.save()

        # Create and save a new entity
        entity = models.Entity(room=models.Room.objects.get(id=1), name=username)
        entity.save()

        # Create and save a new player
        player = models.Player(user=user, entity=entity)
        player.save()

        self.sendPacket(packet.OkPacket())

    def _DISCONNECT(self, p: packet.DisconnectPacket):
        """
        Handles packets received when this protocol is in the DISCONNECT state.
        Releases this protocol from the server and informs all other protocols
        of this disconnection. No more code should be executed from this protocol.

        This should never be called directly. Instead it should be handled by
        self.connectionLost.
        """
        disconnecting_username: str = p.payloads[0].value

        # TODO: This is yuck, stop it.
        try:
            disconnecting_proto: 'Moonlapse' = [
                proto for proto in self._others if proto._user.username == disconnecting_username
            ][0]
        except IndexError:
            return

        reason: Optional[Failure] = p.payloads[1].value

        if self._logged_in:
            self.processPacket(packet.DisconnectPacket(disconnecting_username, reason=reason))
            self._logged_in = False

        # Release this protocol from the server
        if disconnecting_proto in self._others:
            self._others.remove(disconnecting_proto)
            self._debug(f"Deleted self from others list")

        # Tell all still connected protocols about this disconnection
        for proto in self._others:
            proto.processPacket(packet.GoodbyePacket(disconnecting_proto._entity.id))

    def broadcast(self, *packets: packet.Packet, including: Tuple[str] = tuple(), excluding: Tuple[str] = tuple()) -> None:
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

        sendto: Set['Moonlapse'] = {p for p in self._others if p._user.username not in excluding}

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

        if (desired_y, desired_x) in self._room.solidmap or not within_bounds(desired_y, desired_x, 0, 0, self._room.height - 1, self._room.width - 1):
            self.sendPacket(packet.DenyPacket("Can't move there"))
            return

        self._entity.y = desired_y
        self._entity.x = desired_x
        self._entity.save()
        current_entities_in_view: Set[models.Entity] = self.get_entities_in_view()

        # For players which were previously in our view but aren't any more, tell them to remove us from their view
        # Also remove them from our view
        for old_entity_in_view in self._visible_entities:
            if old_entity_in_view not in current_entities_in_view:
                # TODO: Tell clients about this
                # self.broadcast(packet.ServerEntityPositionPacket(self._user.username, (-1, -1)), including=(old_username_in_view,))
                self._visible_entities.remove(old_entity_in_view)

        # Tell everyone in view our position has updated or we have entered their view
        # self.broadcast(packet.ServerEntityPositionPacket(self._user.username, self.player.get_position()), including=current_usernames_in_view)

    def get_entities_in_view(self) -> Set[models.Entity]:
        topleft_y, topleft_x = self._entity.y - self._player.view_radius, self._entity.x - self._player.view_radius
        botright_y, botright_x = self._entity.y + self._player.view_radius, self._entity.x + self._player.view_radius
        return {
            proto._entity for proto in self._others if within_bounds(
                proto._entity.y, proto._entity.x, topleft_y, topleft_x, botright_y, botright_x
            )
        }


class EntryError(Exception):
    """
    Raised if there was an error during the login or registration process.
    """
    pass

from twisted.protocols.basic import NetstringReceiver
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

from server.__main__ import MoonlapseServer
import manage
from networking import packet
import models
from networking.logger import Log

from typing import *
import time
from django.forms.models import model_to_dict


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
        self._server: MoonlapseServer = server
        self.others: Set['Moonlapse'] = others

        # Information specific to the player using this protocol
        self.user: Optional[models.User] = None
        self.entity: Optional[models.Entity] = None
        self._visible_entities: Set[models.Entity] = set()

        self.logged_in: bool = False

        # The state of the protocol which gets called as a function to process only the packets 
        # intended to be processed in the protocol's current state. Should only be called in the 
        # self.stringReceived method every time a complete netstring is received and converted to 
        # a packet.
        self.state: Callable = self._GETENTRY

        self.logger: Log = Log()

    def connectionMade(self) -> None:
        super().connectionMade()
        servertime: str = time.strftime('%d %B, %Y %R %p', time.gmtime())
        self.sendPacket(packet.WelcomePacket(f"Welcome to MoonlapseMUD. Server time is {servertime}"))

    def connectionLost(self, reason: Failure = None) -> None:
        super().connectionLost()
        self.state = self._DISCONNECT
        if self.logged_in:
            self.processPacket(packet.DisconnectPacket(self.username, reason=reason.getErrorMessage()))
            self.logged_in = False

    def stringReceived(self, string) -> None:
        """
        Processes data sent from this protocol's client.
        This should never be called directly. It's handled by NetStringReceiver 
        on dataReceived.
        """
        p: packet.Packet = packet.frombytes(string)
        print(f"[{self.username}][{self.state.__name__}][{self.roomname}]: Received packet from my client {p}")
        self.state(p)

    def sendPacket(self, p: packet.Packet) -> None:
        """
        Sends a packet to this protocol's client.
        Call this to communicate information back to the game client application.
        """
        self.transport.write(p.tobytes())
        print(f"[{self.username}][{self.state.__name__}][{self.roomname}]: Sent data to my client: {p.tobytes()}")

    def processPacket(self, p: packet.Packet) -> None:
        """
        Processes packets sent to this protocol from another protocol.
        Call this to communicate with other protocols connected to the main server.
        """
        print(f"[{self.username}][{self.state.__name__}][{self.roomname}]: Received packet from a protocol {p}")
        self.state(p)

    def _PLAY(self, p: packet.Packet) -> None:
        """
        Handles packets received when this protocol is in the PLAY state.
        This should never be called directly and is instead handled by
        stringReceived.
        """
        if isinstance(p, packet.MovePacket):
            self.move(p)
        elif isinstance(p, packet.ServerEntityPositionPacket):
            self.user_exchange(p)
        elif isinstance(p, packet.ChatPacket):
            self.chat(p)
        elif isinstance(p, packet.LogoutPacket):
            self.logout(p)
        elif isinstance(p, packet.GoodbyePacket):
            self.depart_other(p)
        elif isinstance(p, packet.ServerLogPacket):
            self.sendPacket(p)
        elif isinstance(p, packet.MoveRoomsPacket):
            self.move_rooms([(p.payloads[0].value,)])

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
        if username in [proto.user.username for proto in self.others]:
            self.sendPacket(packet.DenyPacket("You are already inhabiting this realm"))
            return

        if not models.User.objects.filter(username=username):
            self.sendPacket(packet.DenyPacket("I don't know anybody by that name"))
            return

        if not models.User.objects.filter(password=password):
            self.sendPacket(packet.DenyPacket("Incorrect password"))
            return

        self.user = models.User.objects.filter(username=username, password=password)[0]

        player = models.Player.objects.filter(userid=self.user.id)[0]
        self.entity = models.Entity.objects.filter(id=player.entityid)[0]
        self.move_rooms(self.entity.roomid)

    def move_rooms(self, roomid):
        print(f"\nmove_rooms(roomid={roomid})\n")
        self._server.moveProtocols(self, roomid)

        self.broadcast(packet.GoodbyePacket(self.user.username), excluding=(self.user,))
        self.entity.roomid = roomid
        self.entity.save()
        self.others = self._server.rooms_protos[roomid]
        self._establish_player_in_world()

    def _establish_player_in_world(self) -> None:
        print(f"\n_establish_player_in_world()\n")
        self.sendPacket(packet.OkPacket())

        # Assign the starting position if not already done
        if None in (self.entity.y, self.entity.x):
            self.entity.y = 0
            self.entity.x = 0
            self.entity.save()

        # Send new data to the client
        self.sendPacket(packet.ServerTickRatePacket(100))
        self.sendPacket(packet.ServerModelPacket(self.entity))

        self.state = self._PLAY
        self.broadcast(packet.ServerLogPacket(f"{self.username} has arrived."))
        self.logged_in = True

    def logout(self, p: packet.LogoutPacket):
        username: str = p.payloads[0].value
        if username == self.username:
            # Tell our client it's OK to log out
            self.sendPacket(packet.OkPacket())
            self.move_rooms([(None,)])
            self.logged_in = False
            self.state = self._GETENTRY

    def depart_other(self, p: packet.GoodbyePacket):
        other_username: str = p.payloads[0].value
        if other_username in self._visible_entities:
            self._visible_entities.pop(other_username)
        self.sendPacket(packet.ServerLogPacket(f"{other_username} has departed."))
        self.sendPacket(p)

    def _register_user(self, username: str, password: str) -> None:
        if models.User.objects.filter(username=username):
            self.sendPacket(packet.DenyPacket("Somebody else already goes by that name"))
            return

        user = models.User(username=username, password=password)
        user.save()

    def _DISCONNECT(self, p: packet.DisconnectPacket):
        """
        Handles packets received when this protocol is in the DISCONNECT state.
        Releases this protocol from the server and informs all other protocols
        of this disconnection. No more code should be executed from this protocol.

        This should never be called directly. Instead it should be handleded by
        self.connectionLost.
        """
        # Release this protocol from the server
        if self.username in self.users.keys():
            del self.users[self.username]
            print(f"[{self.username}][{self.state.__name__}][{self.roomname}]: Deleted self from users list")

        # Tell all still connected protocols about this disconnection
        for protocol in self.users.values():
            if protocol != self:
                protocol.processPacket(packet.GoodbyePacket(self.username))

    def broadcast(self, *packets: packet.Packet, including: Tuple[str] = tuple(), excluding: Tuple[str] = tuple()) -> None:
        """
        Sends packets to all protocols specified in "including" except for the ones for the usernames specified in
        "excluding", if any.
        If no protocols are specified in "including", the default behaviour is to send to *all* protocols on the server
        except for the ones specified in "excluding", if any.

        Examples:
            * broadcast(packet.ServerLogPacket("Hello"), excluding=("Josh",)) will send to every but Josh
            * broadcast(packet.ServerLogPacket("Hello"), including=("Sue", "James")) will send to only Sue and James
            * broadcast(packet.ServerLogPacket("Hello"), including=("Mary",), excluding=("Mary",)) will send to noone
        """
        print(f"[{self.username}][{self.state.__name__}][{self.roomname}]: Broadcasting {packets} to {including if including else 'everyone'} except {excluding}")

        sendto: Dict[str, 'Moonlapse'] = {u: p for u, p in self.users.items() if u not in excluding}
        if including:
            sendto = {k: v for k, v in sendto.items() if k in including}

        for name, protocol in sendto.items():
            for p in packets:
                protocol.processPacket(p)

    def chat(self, p: packet.ChatPacket) -> None:
        """
        Broadcasts a chat message which includes this protocol's connected player username.
        Truncates to 80 characters. Cannot be empty.
        """
        message: str = p.payloads[0].value
        if message.strip() != '':
            message: str = f"{self.username} says: {message[:80]}"
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
        if isinstance(p, packet.MoveUpPacket):
            self.entity.y -= 1
        elif isinstance(p, packet.MoveRightPacket):
            self.entity.x += 1
        elif isinstance(p, packet.MoveDownPacket):
            self.entity.y += 1
        elif isinstance(p, packet.MoveLeftPacket):
            self.entity.x -= 1

        room = self.player.get_room()
        if within_bounds(self.entity.y, self.entity.x, 0, 0, room.height - 1, room.width - 1) and (self.entity.y, self.entity.x) not in room.solidmap:
            self.entity.save()
            current_usernames_in_view: Tuple[str] = self.get_usernames_in_view()

            # For players who were previously in our view but aren't any more, tell them to remove us from their view
            # Also remove them from our view
            for old_username_in_view in list(self._visible_entities.keys()):    # We might change the dict's size during iteration so better convert it to a list
                if old_username_in_view not in current_usernames_in_view:
                    self.broadcast(packet.ServerEntityPositionPacket(self.username, (-1, -1)), including=(old_username_in_view,))
                    self._visible_entities.pop(old_username_in_view)

            # Tell everyone in view our position has updated or we have entered their view
            self.broadcast(packet.ServerEntityPositionPacket(self.username, self.player.get_position()), including=current_usernames_in_view)

        else:
            self.sendPacket(packet.DenyPacket("Can't move there"))

    def user_exchange(self, p: packet.ServerEntityPositionPacket):
        entity: models.Entity = p.payloads[0].value

        # We can't send or receive tuples as JSON so convert it when expecting
        position: Tuple[int, int] = tuple(p.payloads[1].value)

        p = packet.ServerEntityPositionPacket(entity, position)

        self.sendPacket(p)

        if entity not in self._visible_entities:
            self._visible_entities[other_username] = p.payloads[1].value

            if other_username != self.username:
                self.broadcast(packet.ServerEntityPositionPacket(self.username, self.player.get_position()), including=(other_username,))

    def get_usernames_in_view(self) -> Tuple[str]:
        return tuple([username for username in self.users if within_bounds(
            self.users[username].player.get_position(),
            self.player.get_view_range_topleft(),
            self.player.get_view_range_botright()
        )])


class EntryError(Exception):
    """
    Raised if there was an error during the login or registration process.
    """
    pass

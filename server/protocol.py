from twisted.protocols.basic import NetstringReceiver
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

from server.__main__ import MoonlapseServer
from database import Database
from networking import packet
from networking import models
from networking.logger import Log

from typing import *
import time
from maps import Room


def within_bounds(coords: Tuple[int, int], topleft: Tuple[int, int], botright: Tuple[int, int]) -> bool:
    """
    Checks if the given coordinates are inside the square defined by the top left and bottom right corners.
    Includes all values in the square, even right/bottom-most parts.
    """
    return topleft[0] <= coords[0] <= botright[0] and topleft[1] <= coords[1] <= botright[1]


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
    def __init__(self, server: MoonlapseServer, database: Database, roomname: Optional[str] = None):
        super().__init__()
        self._server: MoonlapseServer = server
        self.database: Database = database
        self.roomname = roomname

        # A volatile dictionary of usernames to protocols passed in by the server.
        self.users: Dict[str, 'Moonlapse'] = {}

        # Information specific to the player using this protocol
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.player: Optional[models.Player] = None
        self.players_visible_users: Dict[str, Tuple[int, int]] = {}
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
        self.sendPacket(packet.WelcomePacket(f"Welcome to MoonlapseMUD 0.2 - Server time: {servertime}"))

    def connectionLost(self, reason: Failure = None) -> None:
        super().connectionLost()
        self.state = self._DISCONNECT
        if self.logged_in:
            self.processPacket(packet.DisconnectPacket(self.username, reason=reason.getErrorMessage()))

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
        elif isinstance(p, packet.ServerUserPositionPacket):
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
            self._handle_login(p.payloads[0].value, p.payloads[1].value)
        elif isinstance(p, packet.RegisterPacket):
            self._handle_registration(p.payloads[0].value, p.payloads[1].value)

    def _handle_login(self, username: str, password: str) -> None:
        """
        Handles a login packet by doing the following asynchronously:
        1. Check if the given username is already connected to the server
        2. Check if the given username exists in the database
        3. Check if the given password is correct for the given username
        4. Initialise the player
        5. Move the player to the server room the database has them in
        6. Move the player to the position the database has them in
        7. Send all of the gathered information to the client

        If an error occurs at any point in the process, it is sent as a Deny Packet back
        to the client with an appropriate error message.
        """
        if username in self.users.keys():
            self.sendPacket(packet.DenyPacket("You are already inhabiting this realm"))
            return

        self.database.user_exists(username
        ).addCallbacks(
            callback = self._check_password_correct,
            callbackArgs = (username, password),
            errback = lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage()))  # Catch user_exists
        ).addCallbacks(
            callback = self._initialise_player_and_query_room,
            callbackArgs = (username,),
            errback = lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage()))  # Catch check_password_correct
        ).addCallbacks(
            callback = self.move_rooms,
            errback = lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage()))  # Catch initialise_player_and_query_room
        )

    def _check_password_correct(self, user_exists: List[Tuple[bool]], username: str, password: str) -> Deferred:
        print(f"\n_check_password_correct(user_exists={user_exists}, username={username}, password={password})\n")
        if user_exists and not user_exists[0][0]:
            raise EntryError("I don't know anybody by that name")

        return self.database.password_correct(username, password)

    def _initialise_player_and_query_room(self, password_correct: List[Tuple[bool]], username: str) -> Deferred:
        print(f"\n_initialise_player_and_query_room(password_correct={password_correct}, username={username})\n")
        if password_correct and not password_correct[0][0]:
            raise EntryError("Incorrect password")

        self.username = username
        self.player = models.Player(self.username)

        return self.database.get_player_roomname(username)

    def move_rooms(self, roomname: List[Tuple[str]]):
        print(f"\nmove_rooms(roomname={roomname})\n")
        roomname = roomname[0][0]
        self.broadcast(packet.GoodbyePacket(self.username), excluding=(self.username,))
        self._server.moveProtocols(self, roomname)
        self.roomname = roomname
        self.users = self._server.roomnames_users[roomname]
        self.player.set_room(Room(roomname))

        self.database.set_player_room(self.username, roomname
        ).addCallbacks(
            callback=self.query_player_position,
            errback=lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage()))  # Catch move_rooms
        ).addCallbacks(
            callback=self._establish_player_in_world,
            errback=lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage()))  # Catch query_player_position
        )

    def query_player_position(self, _):
        print(f"\nquery_player_position(_={_})\n")
        return self.database.get_player_pos(self.username)

    def _establish_player_in_world(self, init_pos: List[Tuple[Optional[float], Optional[float]]]) -> None:
        print(f"\n_establish_player_in_world(init_pos={init_pos})\n")
        self.sendPacket(packet.OkPacket())

        if init_pos:
            init_pos: Tuple[Optional[float], Optional[float]] = init_pos[0]
            print(f"[{self.username}][{self.state.__name__}][{self.roomname}]: Got", init_pos)
            self.player.set_view_radius(10)

            if None in init_pos:
                self.player.assign_location(init_pos)
                new_pos: Tuple[int, int] = self.player.get_position()
                self.database.update_player_pos(self.username, new_pos[0], new_pos[1])
            else:
                init_pos = (int(init_pos[0]), int(init_pos[1]))
                self.player.assign_location(init_pos)

        self.sendPacket(packet.ServerTickRatePacket(100))
        self.player.get_room().pack()
        self.sendPacket(packet.ServerPlayerPacket(self.player))
        self.player.get_room().unpack()

        self.state = self._PLAY
        self.broadcast(packet.ServerUserPositionPacket(self.username, self.player.get_position()), excluding=(self.username,))
        self.broadcast(packet.ServerLogPacket(f"{self.username} has arrived."))
        self.logged_in = True

    def logout(self, p: packet.LogoutPacket):
        username: str = p.payloads[0].value
        if username == self.username:
            # If the player to logout it ourselves, tell all other protocols
            for protocol in self.users.values():
                if protocol != self:
                    protocol.processPacket(p)

            self.sendPacket(packet.OkPacket())
            del self.users[self.username]
            self.username = None
            self.password = None
            self.player = None
            self.logged_in = False
            self.state = self._GETENTRY

        else:
            # If the player to logout is not ourselves, handle things differently
            self.logout_other(p)

    def depart_other(self, p: packet.GoodbyePacket):
        other_name: str = p.payloads[0].value if p.payloads[0].value else 'Someone'
        self.sendPacket(packet.ServerLogPacket(f"{other_name} has departed."))
        self.sendPacket(p)

    def logout_other(self, p: packet.LogoutPacket):
        other_name: str = p.payloads[0].value if p.payloads[0].value else 'Someone'
        self.sendPacket(packet.ServerLogPacket(f"{other_name} has departed..."))
        self.sendPacket(p)

    def _handle_registration(self, username: str, password: str) -> None:
        """
        Handles a registration packet by doing the following asynchronously:
        1. Check if the given username does not already exist in the database
        2. Write the new username and password into the database
        3. Tell the client the registration was successful

        If an error occurs at any point in the process, it is sent as a Deny Packet back
        to the client with an appropriate error message.
        """
        self.database.user_exists(username
        ).addCallbacks(
            callback=self._register_user,
            callbackArgs=(username, password),
            errback=lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage()))  # Catch user_exists
        ).addCallbacks(
            callback=lambda _: self.sendPacket(packet.OkPacket()),
            errback=lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage()))  # Catch register_user
        )

    def _register_user(self, user_exists: List[Tuple[bool]], username: str, password: str) -> Deferred:
        if user_exists[0][0]:
            raise EntryError(f"Somebody else already goes by that name")

        return self.database.register_user(username, password)

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
        pos: Tuple[int, int] = self.player.get_position()

        # Calculate the desired destination
        dest: List[int] = list(pos)
        if isinstance(p, packet.MoveUpPacket):
            dest[0] -= 1
        elif isinstance(p, packet.MoveRightPacket):
            dest[1] += 1
        elif isinstance(p, packet.MoveDownPacket):
            dest[0] += 1
        elif isinstance(p, packet.MoveLeftPacket):
            dest[1] -= 1

        room = self.player.get_room()
        if within_bounds(tuple(dest), (0, 0), (room.height - 1, room.width - 1)) and tuple(dest) not in room.solidmap:
            self.player.set_position(dest)
            self.database.update_player_pos(self.username, dest[0], dest[1])

            current_usernames_in_view: Tuple[str] = self.get_usernames_in_view()

            # For players who were previously in our view but aren't any more, tell them to remove us from their view
            # Also remove them from our view
            for old_username_in_view in list(self.players_visible_users.keys()):    # We might change the dict's size during iteration so better convert it to a list
                if old_username_in_view not in current_usernames_in_view:
                    self.broadcast(packet.ServerUserPositionPacket(self.username, (-1, -1)), including=(old_username_in_view,))
                    self.players_visible_users.pop(old_username_in_view)

            # Tell everyone in view our position has updated or we have entered their view
            self.broadcast(packet.ServerUserPositionPacket(self.username, self.player.get_position()), including=current_usernames_in_view)

        else:
            self.sendPacket(packet.DenyPacket("can't move there"))

    def user_exchange(self, p: packet.ServerUserPositionPacket):
        # We can't send or receive tuples as JSON so convert it when expecting
        p = packet.ServerUserPositionPacket(p.payloads[0].value, tuple(p.payloads[1].value))

        self.sendPacket(p)

        other_username: str = p.payloads[0].value
        if other_username not in self.players_visible_users:
            self.players_visible_users[other_username] = p.payloads[1].value

            if other_username != self.username:
                self.broadcast(packet.ServerUserPositionPacket(self.username, self.player.get_position()), including=(other_username,))

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

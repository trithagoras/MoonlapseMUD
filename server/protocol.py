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
import os
import maps


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
    def __init__(self, server: MoonlapseServer, database: Database, users: Dict[str, 'Moonlapse']):
        super().__init__()
        self._server: MoonlapseServer = server
        self.database: Database = database
        self.logger: Log = Log()

        # A volatile dictionary of usernames to protocols passed in by the server.
        self.users: Dict[str, 'Moonlapse'] = users

        # Information specific to the player using this protocol
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.player: Optional[models.Player] = None
        self.logged_in: bool = False

        # The state of the protocol which gets called as a function to process only the packets 
        # intended to be processed in the protocol's current state. Should only be called in the 
        # self.stringReceived method every time a complete netstring is received and converted to 
        # a packet.
        self.state: Callable = self._GETENTRY

        # Load in the map files and convert them to palatable data types to be sent out to the client.
        pwd: str = os.path.dirname(__file__)
        ground_map_fn: str = os.path.join(pwd, '..', 'maps', 'forest_ground.ml')
        with open(ground_map_fn, 'r') as f:
            self.ground_map_file = [line.strip('\n') for line in f.readlines()]

        solid_map_fn: str = os.path.join(pwd, '..', 'maps', 'forest_solid.ml')
        with open(solid_map_fn, 'r') as f:
            self.solid_map_file = [line.strip('\n') for line in f.readlines()]

        # Load the coordinates of each type of ground material into a dictionary
        # Should be accessed like self.ground_map_data[maps.STONE] which will return all coordinates where
        # stone is found.
        asciilist = maps.ml2asciilist(self.ground_map_file)
        self.map_height = len(asciilist)
        self.map_width = len(asciilist[0])
        self.ground_map_data: Dict[chr, List[List[int]]] = {}
        for y, row in enumerate(asciilist):
            for x, c in enumerate(row):
                if c in self.ground_map_data.keys():
                    self.ground_map_data[c].append([y, x])
                else:
                    self.ground_map_data[c] = [[y, x]]


        # Repeat for solid and roof map data
        asciilist = maps.ml2asciilist(self.solid_map_file)
        self.solid_map_data: Dict[chr, List[List[int]]] = {}
        for y, row in enumerate(asciilist):
            for x, c in enumerate(row):
                if c in self.solid_map_data.keys():
                    self.solid_map_data[c].append([y, x])
                else:
                    self.solid_map_data[c] = [[y, x]]

    def connectionMade(self) -> None:
        super().connectionMade()
        servertime: str = time.strftime('%d %B, %Y %R %p', time.gmtime())
        self.sendPacket(packet.WelcomePacket(f"Welcome to MoonlapseMUD - Server time: {servertime}"))

    def connectionLost(self, reason: Failure = None) -> None:
        super().connectionLost()
        self.state = self._DISCONNECT
        if self.logged_in:
            self.processPacket(packet.DisconnectPacket(self.player, reason=reason.getErrorMessage()))

    def stringReceived(self, string) -> None:
        """
        Processes data sent from this protocol's client.
        This should never be called directly. It's handled by NetStringReceiver 
        on dataReceived.
        """
        p: packet.Packet = packet.frombytes(string)
        print(f"[{self.username}][{self.state.__name__}][{self.users.keys()}]: Received packet from my client {p}")
        self.state(p)

    def sendPacket(self, p: packet.Packet) -> None:
        """
        Sends a packet to this protocol's client. 
        Call this to communicate information back to the game client application.
        """
        self.transport.write(p.tobytes())
        print(f"[{self.username}][{self.state.__name__}][{self.users.keys()}]: Sent data to my client: {p.tobytes()}")

    def processPacket(self, p: packet.Packet) -> None:
        """
        Processes packets sent to this protocol from another protocol.
        Call this to communicate with other protocols connected to the main server.
        """
        print(f"[{self.username}][{self.state.__name__}][{self.users.keys()}]: Received packet from a protocol {p}")
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
        elif isinstance(p, packet.HelloPacket):
            self.welcome(p)
        elif isinstance(p, packet.LogoutPacket):
            self.logout(p)
        elif isinstance(p, packet.DisconnectPacket):
            self.disconnect_other(p)

    def _GETENTRY(self, p: Union[packet.LoginPacket, packet.RegisterPacket]) -> None:
        """
        Handles packets received when this protocol is in the GETENTRY state.
        This should never be called directly and is instead handled by 
        stringReceived.
        """
        username: str = p.payloads[0].value
        password: str = p.payloads[1].value

        if isinstance(p, packet.LoginPacket):
            self._handle_login(username, password)
        elif isinstance(p, packet.RegisterPacket):
            self._handle_registration(username, password)

    def _handle_login(self, username: str, password: str) -> None:
        """
        Handles a login packet by doing the following asynchronously:
        1. Check if the given username is already connected to the server
        2. Check if the given username exists in the database
        3. Check if the given password is correct for the given username
        4. Initialises the new player in this protocol by setting some instance 
           variables
        5. Establishes the new player in the room and sends information back to the 
           game client

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
            errback = lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage())) # Catch user_exists
        ).addCallbacks(
            callback = self._initialise_player, 
            callbackArgs=(username,), 
            errback = lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage())) # Catch check_password_correct
        ).addCallbacks(
            callback = self._establish_player_in_world, 
            errback = lambda e: self.sendPacket(packet.DenyPacket(e.getErrorMessage()))  # Catch initialise_new_player
        )

    def _check_password_correct(self, user_exists: List[Tuple[bool]], username: str, password: str) -> Deferred:
        if not user_exists[0][0]:
            raise EntryError("I don't know anybody by that name")

        return self.database.password_correct(username, password)

    def _initialise_player(self, password_correct: List[Tuple[bool]], username: str) -> Deferred:
        print(f"_initialise_player(password_correct={password_correct}, username={username})")
        if not password_correct[0][0]:
            raise EntryError("Incorrect password")
        
        self.sendPacket(packet.OkPacket())

        self.username = username

        self.users[self.username] = self

        # Assign the lowest available ID to this new player
        ids: List[int] = [-1 if protocol.player is None else protocol.player.get_id() for protocol in self.users.values()]
        id = 0
        while id in ids:
            id += 1
        self.player = models.Player(id)

        self.player.assign_username(self.username)
        
        return self.database.get_player_pos(self.player)

    def _establish_player_in_world(self, init_pos: List[Tuple[int]]) -> None:
        print(f"[{self.username}][{self.state.__name__}][{self.users.keys()}]: Got", init_pos)
        init_pos = init_pos[0]
        self.player.assign_location(list(init_pos), list(self.solid_map_data.keys()), self.map_height, self.map_width)

        if init_pos == (None, None):
            pos = self.player.get_position()
            self.database.update_player_pos(self.player, pos[0], pos[1])

        self.sendPacket(packet.ServerGroundMapFilePacket(self.ground_map_file))
        self.sendPacket(packet.ServerSolidMapFilePacket(self.solid_map_file))
        self.sendPacket(packet.ServerTickRatePacket(100))
        self.sendPacket(packet.ServerPlayerPacket(self.player))

        for protocol in self.users.values():
            if protocol != self:
                protocol.processPacket(packet.HelloPacket(self.player))

        self.broadcast(f"{self.username} has arrived.")
        self.logged_in = True
        self.state = self._PLAY

    def logout(self, p: packet.LogoutPacket):
        username: str = p.payloads[0].value
        if username == self.username:
            # If the player to logout it ourselves, tell all other protocols
            for protocol in self.users.values():
                if protocol != self:
                    protocol.processPacket(p)

            self.sendPacket(packet.GoodbyePacket())
            del self.users[self.username]
            self.username = None
            self.password = None
            self.player = None
            self.logged_in = False
            self.state = self._GETENTRY

        else:
            # If the player to logout is not ourselves, handle things differently
            self.logout_other(p)

    def disconnect_other(self, p: packet.DisconnectPacket):
        other_player: Optional[models.Player] = p.payloads[0].value
        other_name: str = other_player.get_username() if other_player else 'Someone'
        reason: Optional[str] = p.payloads[1].value
        self.sendPacket(packet.ServerLogPacket(f"{other_name} has disconnected{': ' + reason if reason else ''}."))
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
            print(f"[{self.username}][{self.state.__name__}][{self.users.keys()}]: Deleted self from users list")

        # Tell all still connected protocols about this disconnection
        for protocol in self.users.values():
            if protocol != self:
                protocol.processPacket(p)

    def broadcast(self, message: str) -> None:
        """
        Sends a message to all clients connected to the server.
        """
        for name, protocol in self.users.items():
            protocol.sendPacket(packet.ServerLogPacket(message))

        self.logger.log(message)

    def chat(self, p: packet.ChatPacket) -> None:
        """
        Broadcasts a chat message which includes this protocol's connected player username.
        Truncates to 80 characters. Cannot be empty.
        """
        message: str = p.payloads[0].value
        if message.strip() != '':
            message: str = f"{self.username} says: {message[:80]}"
            self.broadcast(message)

    def move(self, p: packet.MovePacket) -> None:
        """
        Updates this protocol's player's position and sends the player back to all 
        clients connected to the server.

        NOTE: This method should be avoided in a future release to prevent sending more
              information than is required. A client will know all the information 
              about every player connected to the server even if they are not in view.
        """
        pos: Tuple[int] = self.player.get_position()

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

        if self._within_bounds(dest) and tuple(dest) not in self.solid_map_data.keys():
            self.player.set_position(dest)
            d: Deferred = self.database.update_player_pos(self.player, dest[0], dest[1])

            for name, protocol in self.users.items():
                protocol.sendPacket(packet.ServerPlayerPacket(self.player))
        else:
            self.sendPacket(packet.DenyPacket("can't move there"))

    def _within_bounds(self, coords: List[int]) -> bool:
        return 0 <= coords[0] < self.map_height and 0 <= coords[1] < self.map_width

    def welcome(self, p: packet.HelloPacket):
        """
        Called whenever a new protocol joins the server. They will tell this protocol about their 
        player and this protocol tells them about its player in return.
        """
        new_player: models.Player = p.payloads[0].value
        new_protocol: Optional['Moonlapse'] = None

        # Get the protocol which sent the packet
        for protocol in self.users.values():
            if protocol.player == new_player:
                new_protocol = protocol
                break
        
        # Return if no match found
        if not new_protocol:
            print(f"[{self.player.get_username()}] Could not find protocol attached to new player to welcome ({new_player.get_username()})")
            return

        # Send the client player information for the newly connecting protocol
        self.sendPacket(packet.ServerPlayerPacket(new_player))
        
        # Send the newly connecting protocol information for this protocol's player
        new_protocol.sendPacket(packet.ServerPlayerPacket(self.player))
        print(f"[{self.player.get_username()}] Welcomed new player {new_player.get_username()}")


class EntryError(Exception):
    """
    Raised if there was an error during the login or registration process.
    """
    pass

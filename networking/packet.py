import traceback
import json

from . import payload
from .payload import Payload
from typing import *


class Packet:
    """
    A custom Packet data type encapsulating a netstring. See http://cr.yp.to/proto/netstrings.txt for
    the specification of netstrings.

    Every netstring starts with decimal digits that specify the length of the rest of the data. This
    length specification is separated from the data by a colon. The data is terminated with a comma.

    You can send a packet using the self.tobytes method which will pickle all payloads and format it
    into a netstring. On the receiving end, you can use the module's frombytes function which reverses
    the pickling and constructs the data back into the specific packet type (one of the standard
    implementations defined in this module).

    The receiving end should make use of this module's receive function to ensure the entire data is
    received and nothing more than that.

    For example:
        From the client:
            loginpacket: packet.LoginPacket = LoginPacket("username", "password")
            netstring: bytes = loginpacket.tobytes()
            server_socket.send(netstring)
        From the server:
            netstring: bytes = packet.receive(client_socket)
            loginpacket: packet.LoginPacket = packet.frombytes(netstring)
            dostuff(loginpacket)

    When receiving packets, always use python's built-in isinstance function to execute code blocks
    specific to the packet type you're after. For example, a protocol's stringReceived method might
    look like this:
        def stringReceived(netstring: bytes):
            p: packet.Packet = packet.frombytes(netstring)
            if isinstance(p, packet.LoginPacket):
                self.login(p)
            elif isinstance(p, packet.RegisterPacket):
                self.register(p)
            ...
    """
    MAX_LENGTH: int = 2 ** 63 - 1

    def __init__(self, *payloads: Payload):
        self.action: str = type(self).__name__
        self.payloads: Tuple[Payload] = payloads

    def tobytes(self) -> bytes:
        serialize_dict: Dict[str, str] = {'a': self.action}
        for i in range(len(self.payloads)):
            serialize_dict[f'p{i}'] = self.payloads[i].serialize()
        data = json.dumps(serialize_dict, separators=(',', ':')).encode('utf-8')
        return data

    def __repr__(self) -> str:
        return f"{self.action}: {self.payloads}"


class OkPacket(Packet):
    """
    A packet sent from a protocol to a client to signify it's OK to proceed and there were no errors.
    """
    pass


class DenyPacket(Packet):
    """
    A packet sent from a protocol to a client to signify there was an error with the request and it
    shouldn't proceed. An optional reason can be supplied which the client should probably display
    to the user.
    """

    def __init__(self, reason: str = "unspecified"):
        super().__init__(Payload(reason))


class WelcomePacket(Packet):
    """
    A packet sent from a protocol to a client after a connection is established. An optional message
    of the day can be supplied which the client can display to the user.
    """

    def __init__(self, motd: str = "Welcome to MoonlapseMUD"):
        super().__init__(Payload(motd))


class GoodbyePacket(Packet):
    """
    A packet sent from a protocol to a client after a moving rooms. Can also be sent from a protocol to
    a client to indicate someone else has left the room.
    """

    def __init__(self, instanceid: int):
        super().__init__(Payload(instanceid))


class LoginPacket(Packet):
    """
    A packet sent from a client to a protocol to request a login.
    """

    def __init__(self, username, password: str):
        pusername = Payload(username)
        ppassword = Payload(password)
        super().__init__(pusername, ppassword)

    def __repr__(self):
        return f"{self.action}: ({self.payloads[0]}, (Payload: ***))"


class LogoutPacket(Packet):
    def __init__(self, username: str):
        super().__init__(Payload(username))


class RegisterPacket(Packet):
    """
    A packet sent from a client to a protocol to request registration. Note that this is identical
    technically to the LoginPacket but it's important to have a separate name to distinguish the
    different use cases when handling these packets on the protocol's end.
    """

    def __init__(self, username, password: str):
        pusername = Payload(username)
        ppassword = Payload(password)
        super().__init__(pusername, ppassword)

    def __repr__(self):
        return f"{self.action}: ({self.payloads[0]}, (Payload: ***))"


class ServerModelPacket(Packet):
    """
    A packet representing a model from the server in the form of a dictionary.
    Example of an Entity model from the server in this form:
    {
        "id": 12,
        "roomid": 3,
        "y": 24,
        "x": 1,
        "char": "@"
    }
    """

    def __init__(self, type: str, modeldict: dict):
        ptype: Payload = Payload(type)
        pmodel: Payload = Payload(modeldict)
        super().__init__(ptype, pmodel)


class HelloPacket(Packet):
    """
    A packet representing an entity model from the server in the form of a dictionary.
    Use only to broadcast yourself when first connecting to a new room.
    """

    def __init__(self, modeldict: dict):
        pmodel: Payload = Payload(modeldict)
        super().__init__(pmodel)


class ChatPacket(Packet):
    """
    A packet sent from a client or a protocol to communicate a player's chat message to other players.
    The message is truncated to the first 80 characters.
    """

    def __init__(self, message: str):
        pmessage: Payload = Payload(message[:80])
        super().__init__(pmessage)


class MovePacket(Packet):
    """
    This class should not be instantiated directly but instead one of its implementations below should.
    """
    pass


class MoveUpPacket(MovePacket):
    """
    A packet sent from a client to its protocol to request an up movement.
    """
    pass


class MoveDownPacket(MovePacket):
    """
    A packet sent from a client to its protocol to request a down movement.
    """
    pass


class MoveLeftPacket(MovePacket):
    """
    A packet sent from a client to its protocol to request a left movement.
    """
    pass


class MoveRightPacket(MovePacket):
    """
    A packet sent from a client to its protocol to request a right movement.
    """
    pass


class MoveRoomsPacket(Packet):
    def __init__(self, roomid: Optional[int]):
        super().__init__(Payload(roomid))


class DisconnectPacket(Packet):
    """
    A packet sent to signify the client's connection has been lost. An optional reason
    can be supplied which could be displayed to other clients.
    """

    def __init__(self, username: str, reason: Optional[str] = None):
        pusername: Payload = Payload(username)
        preason: Payload = Payload(reason)
        super().__init__(pusername, preason)


class ServerLogPacket(Packet):
    """
    A packet sent from a protocol to a client to convey a server-specific message.
    """

    def __init__(self, log: str):
        super().__init__(Payload(log))


class ServerRoomFullPacket(Packet):
    """
    A packet sent from a protocol to its client to indicate the room it's trying to join
    is at maximum capacity.
    """

    def __init__(self):
        super().__init__()


class ServerTickRatePacket(Packet):
    """
    A packet sent from a protocol to its client describing the tick rate of the room it's connected to. This
    should be interpreted by the game client for handling input and refreshing the screen, etc.
    """

    def __init__(self, tickrate: int):
        super().__init__(Payload(tickrate))


class ClientKeyPacket(Packet):
    """
    A packet sent from a protocol to its client with the client's public key used in encrypting traffic.
    """

    def __init__(self, n: int, e: int):
        super().__init__(Payload(n), Payload(e))


class GrabItemPacket(Packet):
    """
    A packet send from a client to its protocol to pick up an item off the ground where the player is
    """

    def __init__(self):
        super().__init__()


class WeatherChangePacket(Packet):
    """
    A packet send from a protocol to its client to indicate change in weather

    possible weathers:
    - Clear
    - Rain
    - Storm
    """

    def __init__(self, new_weather: str):
        super().__init__(Payload(new_weather))


def frombytes(data: bytes) -> Packet:
    """
    Constructs a proper packet type from bytes encoding a netstring. See
    http://cr.yp.to/proto/netstrings.txt for the specification of netstrings.

    Every netstring starts with decimal digits that specify the length of the rest of the data. This
    length specification is separated from the data by a colon. The data is terminated with a comma.

    The payload is automatically pickled and converted to a hex string in order to be sent over
    the network. This allows you to send and receive all picklable Python objects.
    """
    obj_dict: Dict[str, str] = json.loads(data)

    action: Optional[str] = None
    payloads_values: List[Optional[Any]] = []
    for key, value in obj_dict.items():
        if key == 'a':
            action = value

        elif key[0] == 'p':
            index: int = int(key[1:])
            payloads_values.insert(index, payload.deserialize(value).value)

    # Use reflection to construct the specific packet type we're looking for
    specificPacketClassName: str = action
    try:
        constructor: Type = globals()[specificPacketClassName]
        rPacket = constructor(*payloads_values)
        return rPacket
    except KeyError:
        print(f"KeyError: {specificPacketClassName} is not a valid packet name. Stacktrace: ")
        print(traceback.format_exc())
    except TypeError:
        print(f"TypeError: {specificPacketClassName} can't handle arguments {tuple(payloads_values)}.")

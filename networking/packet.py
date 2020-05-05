from typing import *
import json
import socket
import traceback
import pickle

from .payload import *
from .models import *


class Packet:
    MAX_LENGTH: int = 2 ** 63 - 1
        
    def __init__(self, *payloads: Payload):
        self.action: str = type(self).__name__
        self.payloads: Tuple[Payload] = payloads

    def tobytes(self) -> str:
        serialize_dict: Dict[str, str] = {}
        serialize_dict['a'] = self.action
        for i in range(len(self.payloads)):
            serialize_dict[f'p{i}'] = self.payloads[i].serialize()
        datastr: str = json.dumps(serialize_dict, separators=(',', ':'))
        lengthstr: str = str(len(datastr))
        return str.encode(lengthstr + ':' + datastr + ',', 'utf-8')

    
    def __repr__(self) -> str:
        return f"{self.action}: {self.payloads}"


class OkPacket(Packet):
    pass


class DenyPacket(Packet):
    def __init__(self, reason: str = "unspecified"):
        super().__init__(Payload(reason))


class WelcomePacket(Packet):
    def __init__(self, motd: str = "Welcome to MoonlapseMUD"):
        super().__init__(Payload(motd))


class LoginPacket(Packet):
    def __init__(self, username, password: str):
        pusername = Payload(username)
        ppassword = Payload(password)
        super().__init__(pusername, ppassword)

class RegisterPacket(Packet):
    def __init__(self, username, password: str):
        pusername = Payload(username)
        ppassword = Payload(password)
        super().__init__(pusername, ppassword)

class ChatPacket(Packet):
    def __init__(self, message: str):
        pmessage: Payload = Payload(message[:80])
        super().__init__(pmessage)


class MovePacket(Packet):
    def __init__(self, player: Player, direction: chr):
        """
        A packet which takes a direction with intention to move a player in that direction.
        Accepted directions include: 'u' (up), 'd' (down), 'l' (left), 'r' (right, default).

        :param player:    The player with the intention to move.
        :param direction: The direction to move in. Should be one of 'u', 'd', 'l', 'r'. If 
                          it is not one of those values, the default resulting direction is 
                          right.
        """
        pplayer: Payload = Payload(player)
        pdirection: StdPayload = None
        if direction == 'u':
            pdirection = StdPayload.MOVE_UP
        elif direction == 'd':
            pdirection = StdPayload.MOVE_DOWN
        elif direction == 'l':
            pdirection = StdPayload.MOVE_LEFT
        elif direction == 'r':
            pdirection = StdPayload.MOVE_RIGHT 
        else:
            raise ValueError(f"direction {direction} must be one of 'u', 'd', 'l', 'r'")

        super().__init__(pplayer, pdirection)


class DisconnectPacket(Packet):
    def __init__(self):
        super().__init__()


class ServerLogPacket(Packet):
    def __init__(self, log: str):
        super().__init__(Payload(log))


class ServerRoomFullPacket(Packet):
    def __init__(self):
        super().__init__()


class ServerRoomPlayerPacket(Packet):
    def __init__(self, player: Player):
        super().__init__(Payload(player))


class HelloPacket(Packet):
    def __init__(self, player: Player):
        super().__init__(Payload(player))


class ServerRoomGeometryPacket(Packet):
    """
        Something like {
            "walls": [[1, 2], [3, 4]],
            "grass": [[2, 2], [4, 4], [4, 6]]
        }
    """
    def __init__(self, geometry: Dict[str, List[List[int]]]):
        super().__init__(Payload(geometry))


class ServerRoomSizePacket(Packet):
    def __init__(self, height: int, width: int):
        pheight: Payload = Payload(height)
        pwidth: Payload = Payload(width)
        super().__init__(pheight, pwidth)


class ServerRoomTickRatePacket(Packet):
    def __init__(self, tickrate: int):
        super().__init__(Payload(tickrate))


def frombytes(data: bytes) -> Packet:
    """
    Constructs a proper packet type from bytes encoding a utf-8 string formatted like so:
    {"a":"PacketClassName","p0":"A payload","p1":"Another payload"}

    The payload is automatically pickled and converted to a hex string in order to be sent over 
    the network. This allows you to send and receive all picklable Python objects.
    """
    obj_dict: Dict[str, str] = json.loads(data)

    action: Optional[str] = None
    payloads: List[Optional[Payload]] = []
    for key in obj_dict:
        value: str = obj_dict[key]
        if key == 'a':
            action = value
        elif key[0] == 'p':
            index: int = int(key[1:])
            payloadbytes = bytes.fromhex(value)
            payloads.insert(index, pickle.loads(payloadbytes))
    
    # Use reflection to construct the specific packet type we're looking for
    specificPacketClassName:str = action
    try:
        constructor: Type = globals()[specificPacketClassName]
        rPacket = constructor(*tuple(payloads))
        return rPacket
    except KeyError:
        print(f"KeyError: {specificPacketClassName} is not a valid packet name. Stacktrace: ")
        print(traceback.format_exc())

def send(p: Packet, s: socket.socket) -> str:
    failure = s.sendall(p.tobytes())
    if failure is not None:
        print("Failed to send all data", file=sys.stderr)
        send(p, s)
    return p.tobytes()
    

def receive(s: socket.socket):
    length: bytes = b''
    json: bytes = b''
    for i in range(len(str(Packet.MAX_LENGTH))):
        c: bytes = s.recv(1)
        if c != b':':
            try:
                int(c)
            except ValueError:
                raise PacketParseError(f"Error reading packet length. So far got {length} but next digit came in as {c}")
            length += c
        else:
            data: bytes = s.recv(int(length))

            # Perhaps all the data is not received yet
            while len(data) < int(length):
                nextLength = int(length) - len(data)
                data += s.recv(nextLength)

            # Read off the trailing comma
            s.recv(1)

            return frombytes(data)

    raise PacketParseError("Error reading packet length. Too long.")

class PacketParseError(Exception):
    pass

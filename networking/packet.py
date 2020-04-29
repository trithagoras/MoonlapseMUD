from typing import *
import json
import socket as sock
import traceback
import pickle

from .payload import *
from .models import *


class Packet:
    def __init__(self, *payloads: Payload):
        self.action: str = type(self).__name__
        self.payloads: Tuple[Payload] = payloads

    def serialize(self) -> str:
        serialize_dict: Dict[str, str] = {}
        serialize_dict['a'] = self.action
        for i in range(len(self.payloads)):
            serialize_dict[f'p{i}'] = self.payloads[i].serialize()
        return json.dumps(serialize_dict)
    
    def __repr__(self) -> str:
        return f"{self.action}: {self.payloads}"


class LoginPacket(Packet):
    def __init__(self, username, password: str):
        pusername = Payload(username)
        ppassword = Payload(password)
        super().__init__(pusername, ppassword)


class RegisterPacket(Packet):
    def __init__(self, username: str, password: str):
        pusername = Payload(username)
        ppassword = Payload(password)
        super().__init__(pusername, ppassword)


class MovePacket(Packet):
    def __init__(self, direction: chr):
        """
        A packet which takes a direction with intention to move an object in that direction.
        Accepted directions include: 'u' (up), 'd' (down), 'l' (left), 'r' (right, default).

        :param direction: The direction to move in. Should be one of 'u', 'd', 'l', 'r'. If 
                          it is not one of those values, the default resulting direction is 
                          right.
        """
        pdirection: Payload = None
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

        super().__init__(pdirection)


class ChatPacket(Packet):
    def __init__(self, message: str):
        pmessage: Payload(message)
        super().__init__(pmessage)


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
        pheight = Payload(height)
        pwidth = Payload(width)
        super().__init__(pheight, pwidth)


class ServerRoomTickRatePacket(Packet):
    def __init__(self, tickrate: int):
        super().__init__(Payload(tickrate))

def sendpacket(s: sock.socket, packet: Packet) -> None:
    try:
        data: str = packet.serialize() + ';'
        nbytes: int = len(data)
        s.send(bytes(str(nbytes) + data, 'utf-8'))
    except TypeError:
        print("Bro you tried pickling a socket...")
        print(s)
        print(packet)


def receivepacket(s: sock.socket) -> Packet:
    # data should look something like this
    # 35{'a': 'Packet', 'p0': 'Something'};

    # Get the size of the data first
    sizestr: str = ' '
    while sizestr[-1] != '{':
        sizestr += s.recv(1).decode('utf-8')
    size: int = int(sizestr[:-1])

    # Get the next data to size
    data: str = '{' + s.recv(size - 1).decode('utf-8')
    return constructpacket(json.loads(data[:-1]), debug=debug)


def constructpacket(obj_dict: Dict[str, str]) -> Packet:
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

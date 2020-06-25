from typing import *
import json
import socket
import traceback
import pickle
import threading

from .payload import *
from .models import *


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

    def tobytes(self) -> str:
        # serialize_dict: Dict[str, str] = {}
        # serialize_dict['a'] = self.action
        # for i in range(len(self.payloads)):
        #     serialize_dict[f'p{i}'] = self.payloads[i].serialize()
        # datastr: str = json.dumps(serialize_dict, separators=(',', ':'))
        # lengthstr: str = str(len(datastr))
        # return str.encode(lengthstr + ':' + datastr + ',', 'utf-8')
        serialize_dict: Dict[str, str] = {}
        serialize_dict['a'] = self.action
        for i in range(len(self.payloads)):
            serialize_dict[f'p{i}'] = self.payloads[i].serialize()
        data = json.dumps(serialize_dict, separators=(',', ':')).encode('utf-8')

        length = len(data)
        return str(length).encode('ascii') + b':' + data + b','

    
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


class LoginPacket(Packet):
    """
    A packet sent from a client to a protocol to request a login.
    """
    def __init__(self, username, password: str):
        pusername = Payload(username)
        ppassword = Payload(password)
        super().__init__(pusername, ppassword)

class LogoutPacket(Packet):
    pass

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


class DisconnectPacket(Packet):
    """
    A packet sent to signify the client's connection has been lost. An optional message 
    can be supplied which could be displayed to other clients.
    """
    def __init__(self, player: Player, message: str = "Someone has departed..."):
        pplayer: Payload = Payload(player)
        pmessage: Payload = Payload(f"{player.get_username()} has departed...")
        super().__init__(pplayer, pmessage)


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


class ServerRoomPlayerPacket(Packet):
    """
    A packet sent from a protocol to a client containing an entire models.Player object.
    """
    def __init__(self, player: Player):
        super().__init__(Payload(player))


class HelloPacket(Packet):
    """
    A packet sent from a protocol to another protocol when a player first connects. 
    Each protocol can then update their clients accordingly, i.e. sending their Players 
    in return and telling their clients to add the new Player to the game.
    """
    def __init__(self, player: Player):
        super().__init__(Payload(player))


class ServerRoomGeometryPacket(Packet):
    """
    A packet sent from a protocol to its client describing the geometry of the room it's connected to.
    This should be interpreted by the game client for drawing to the screen, etc.
    Something like {
        "walls": [[1, 2], [3, 4]],
        "grass": [[2, 2], [4, 4], [4, 6]]
    }
    """
    def __init__(self, geometry: Dict[str, List[List[int]]]):
        super().__init__(Payload(geometry))


class ServerRoomSizePacket(Packet):
    """
    A packet sent from a protocol to its client describing the height and width of the room it's connected 
    to. Ths should be interpreted by the game client for drawing to the screen, etc.
    """
    def __init__(self, height: int, width: int):
        pheight: Payload = Payload(height)
        pwidth: Payload = Payload(width)
        super().__init__(pheight, pwidth)


class ServerRoomTickRatePacket(Packet):
    """
    A packet sent from a protocol to its client describing the tick rate of the room it's connected to. This 
    should be interpreted by the game client for handling input and refreshing the screen, etc.
    """
    def __init__(self, tickrate: int):
        super().__init__(Payload(tickrate))


def frombytes(data: bytes) -> Packet:
    """
    Constructs a proper packet type from bytes encoding a netstring. See 
    http://cr.yp.to/proto/netstrings.txt for the specification of netstrings.

    Every netstring starts with decimal digits that specify the length of the rest of the data. This 
    length specification is separated from the data by a colon. The data is terminated with a comma.

    The payload is automatically pickled and converted to a hex string in order to be sent over 
    the network. This allows you to send and receive all picklable Python objects.
    """
    # print(f"Trying to load {data}")
    try:
        obj_dict: Dict[str, str] = json.loads(data)
    except json.decoder.JSONDecodeError as e:
        return
        print(f"Error decoding JSON: attempted to load {data}")
        print(traceback.format_exc())
        return

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
    """
    Converts a Packet to bytes and sends it over a socket. Ensures all the data is sent and no more.
    """
    failure = s.sendall(p.tobytes())
    if failure is not None:
        send(p, s)
    return p.tobytes()
    

def receive(s: socket.socket, debug=False) -> Packet:
    """
    Receives a netstring bytes over a socket. Ensure all data is received and no more. Then 
    converts the data into the original Packet (preserving the exact type from the ones defined 
    in this module) and original payloads depickled as python objects.

    Arguments:
        s {socket.socket} -- The socket to receive netstring-encoded packets over.

    Raises:
        PacketParseError: If the netstring is too long or there was an error reading the length of the 
                          netstring.

    Returns:
        Packet -- The original Packet that was sent with the exact subtype preserved. All original 
                  payloads associated are depickled as python objects.
    """
    if debug:
        f = open('packetdebug.txt', 'a')
    if debug: f.write(f"\nThread {threading.get_ident()}\nPacket.receive({s}, debug={debug})" + '\n')
    length: bytes = b''
    if debug: f.write(f"Initialised length to {length}" + '\n')
    if debug: f.write(f"Entering loop to read packet length" + '\n')
    while len(length) <= len(str(Packet.MAX_LENGTH)):
        c: bytes = s.recv(1)
        if debug: f.write(f"\tReceived byte: {c} (current length: {length})" + '\n')
        if c != b':':
            if debug: f.write(f"\t\tNot b':'" + '\n')
            try:
                int(c)
                if debug: f.write(f"\t\t\tIt's a digit ({int(c)})" + '\n')
            except ValueError:
                if debug: f.write(f"\t\t\tIt's NOT a digit, throwing exception ({c})" + '\n')
                # possible_rest = s.recv(int(2*length))
                if debug: 
                    f.write(f"\t\t\tThere might be more..." + '\n')
                    for i in range(100):
                        f.write(s.recv(1).decode('utf-8'))
                if debug: f.close()
                #raise PacketParseError(f"Error reading packet length. So far got {length} but next digit came in as {c}. The rest is posisbly {possible_rest}.")
            else:
                length += c
                if debug: f.write(f"\t\t\tAppended to length (current length {length}" + '\n')
        else:
            if debug: f.write(f"\t\tIS b':'. Final length to read is {int(length)}" + '\n')
            if len(length) < 1:
                if debug: f.write(f"\t\t\tBut the length is empty! Returning" + '\n')
                return
            data: bytes = s.recv(int(length))
            if debug: f.write(f"\t\tAdded the rest of the {int(length)} bytes to data ({data})" + '\n')


            # Perhaps all the data is not received yet
            if debug: f.write(f"\t\tChecking if all the data's been received" + '\n')
            while len(data) < int(length):
                if debug: f.write(f"\t\t\tMore data to come ({len(data)} < {int(length)})" + '\n')
                nextLength = int(length) - len(data)
                data += s.recv(nextLength)
                if debug: f.write(f"\t\t\tAdded another batch of {nextLength} bytes to data ({data})" + '\n')

            if debug: f.write(f"\t\tAll data's been read ({len(data)} >= {int(length)})" + '\n')

            # Read off the trailing comma
            if debug: f.write(f"\t\tReceiving an extra byte to read off the trailing comma" + '\n')
            s.recv(1)
            if debug: f.write(f"\t\tDone" + '\n')
            if debug: f.write(f"\t\tReturning {frombytes(data)}" + '\n')
            if debug and frombytes(data) is None:
                f.write(f"\t\tThere might be more..." + '\n')
                for i in range(100):
                    f.write(s.recv(1, ).decode('utf-8'))
            if debug: f.close()
            return frombytes(data)

    if debug: f.write(f"\tBroke out of the loop, packet must be too long ({length})" + '\n')
    if debug: f.close()
    #raise PacketParseError("Error reading packet length. Too long.")


class PacketParseError(Exception):
    pass

import random
import string

from Crypto.Cipher import AES
import rsa

from networking import packet


class NetworkState:
    """
    Higher level abstraction for keeping network state. Keeps public_key and socket in neat spot.
    """

    def __init__(self, socket, public_key):
        self.socket = socket
        self.public_key = public_key

    def send_packet(self, p: packet.Packet):
        """
        Converts packet to bytes; then encrypts bytes; then converts to netstring; then send over socket
        :param p: packet to send
        """

        self._send(p, self.socket, self.public_key)

    def receive_packet(self) -> packet.Packet:
        return self._receive(self.socket)

    def _encrypt_message(self, b: bytes, public_key):
        IV = b'1111111111111111'
        key = bytes(
            ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(16)),
            'utf-8')
        aes = AES.new(key, AES.MODE_CFB, IV=IV)

        msg: bytearray = aes.encrypt(b)

        key = rsa.encrypt(key, public_key)
        # key length = 512/8=64 bytes (chars)

        return key + msg

    def _to_netstring(self, data: bytes) -> bytes:
        length = len(data)
        return str(length).encode('ascii') + b':' + data + b','

    def _send(self, p: packet.Packet, s, public_key=None) -> bytes:
        """
        Converts a Packet to bytes and sends it over a socket. Ensures all the data is sent and no more.
        """
        b = p.tobytes()
        if public_key:
            b = self._encrypt_message(b, public_key)

        b = self._to_netstring(b)

        failure = s.sendall(b)
        if failure is not None:
            self._send(p, s)
        return b

    def _receive(self, s) -> packet.Packet:
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
        length: bytes = b''
        while len(length) <= len(str(packet.Packet.MAX_LENGTH)):
            c: bytes = s.recv(1)
            if c != b':':
                try:
                    int(c)
                except ValueError:
                    raise PacketParseError(
                        f"Error reading packet length. So far got {length} but next digit came in as {c}.")
                else:
                    length += c
            else:
                if len(length) < 1:
                    raise PacketParseError(f"Parsing packet but length doesn't seem to be a number. Got {length}.")
                data: bytes = s.recv(int(length))

                # Perhaps all the data is not received yet
                while len(data) < int(length):
                    nextLength = int(length) - len(data)
                    data += s.recv(nextLength)

                # Read off the trailing comma
                s.recv(1)
                return packet.frombytes(data)

        raise PacketParseError("Error reading packet length. Too long.")


class PacketParseError(Exception):
    pass

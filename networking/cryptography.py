import base64
import os
from Crypto import Random
from Crypto.Cipher import AES
from typing import *

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP


BS: int = AES.block_size


def encrypt_aes(raw: bytes, key: bytes) -> bytes:
    raw = _pad(raw.decode('utf-8'))
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(raw.encode()))


def decrypt_aes(enc, key: bytes) -> bytes:
    enc = base64.b64decode(enc)
    iv = enc[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return _unpad(cipher.decrypt(enc))[AES.block_size:]


def _pad(s: str) -> str:
    return s + (BS - len(s) % BS) * chr(BS - len(s) % BS)


def _unpad(s: bytes) -> bytes:
    return s[0:-ord(s[-1:])]


def load_rsa_keypair(directory: str) -> Tuple[RSA.RsaKey, RSA.RsaKey]:
    """
    Returns a pair of public, private RSA keys. If files named id_rsa.pub and rsa_private_key.pem
    already exist in the supplied directory, the returned key-pair will be those keys. If not,
    these files will be created for you in the supplied directory and their contents will be filled
    from a generated key-pair.
    """
    public_key_filename = os.path.join(directory, "id_rsa.pub")
    private_key_filename = os.path.join(directory, "rsa_private_key.pem")

    try:
        with open(public_key_filename, 'rb') as f:
            public_key: RSA.RsaKey = load_rsa_key_from_bytes(f.read())
        with open(private_key_filename, "rb") as f:
            private_key: RSA.RsaKey = load_rsa_key_from_bytes(f.read())

        return public_key, private_key

    except (FileNotFoundError, ValueError):
        # RSA keys haven't been configured yet, or were configured incorrectly. Generate and save new keys.
        key: RSA.RsaKey = RSA.generate(2048)

        with open(public_key_filename, 'wb') as f:
            f.write(key.publickey().export_key('PEM'))
        with open(private_key_filename, 'wb') as f:
            f.write(key.export_key('PEM'))

        return load_rsa_keypair(directory)


def encrypt_rsa(message: bytes, public_key: RSA.RsaKey) -> bytes:
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(message)


def decrypt_rsa(ciphertext: bytes, private_key: RSA.RsaKey) -> bytes:
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(ciphertext)


def load_rsa_key_from_bytes(key_bytes: bytes) -> RSA.RsaKey:
    key: RSA.RsaKey = RSA.import_key(key_bytes)
    return key


def load_rsa_key_from_parts(n: int, e: int) -> RSA.RsaKey:
    key: RSA.RsaKey = RSA.construct(rsa_components=(n, e))
    return key

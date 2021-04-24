import os
import random
import string
import rsa
from Crypto.Cipher import AES
from typing import *

IV = b'1111111111111111'


def load_rsa_keypair(directory: str) -> Tuple[rsa.key.PublicKey, rsa.key.PrivateKey]:
    """
    Returns a pair of public, private RSA keys. If files named id_rsa.pub and rsa_private_key.pem
    already exist in the supplied directory, the returned key-pair will be those keys. If not,
    these files will be created for you in the supplied directory and their contents will be filled
    from a generated key-pair.
    """
    public_key_filename = os.path.join(directory, "id_rsa.pub")
    private_key_filename = os.path.join(directory, "rsa_private_key.pem")
    bit_length: int = 512   # Only 512 works

    try:
        with open(public_key_filename, 'rb') as f:
            public_key = rsa.key.PublicKey.load_pkcs1(f.read())
        with open(private_key_filename, "rb") as f:
            private_key = rsa.key.PrivateKey.load_pkcs1(f.read())

        if public_key.n.bit_length() != bit_length or private_key.n.bit_length() != bit_length:
            raise ValueError(f"Bit length must be {bit_length}")

    except (FileNotFoundError, ValueError):
        # RSA keys haven't been configured yet, or were configured incorrectly. Generate and save new keys.
        public_key, private_key = rsa.key.newkeys(bit_length)

        with open(public_key_filename, 'wb') as f:
            f.write(public_key.save_pkcs1())
        with open(private_key_filename, 'wb') as f:
            f.write(private_key.save_pkcs1())

    return public_key, private_key


def encrypt(message: bytes, public_key: rsa.key.PublicKey):
    aes_key = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(16))
    aes_key = bytes(aes_key, 'utf-8')
    aes = AES.new(aes_key, AES.MODE_CFB, IV=IV)
    msg: bytes = aes.encrypt(message)
    key = rsa.encrypt(aes_key, public_key)
    return key + msg


def decrypt(message: bytes, private_key: rsa.PrivateKey):
    # first 64 bytes is the RSA encrypted AES key; remainder is AES encrypted message
    encrypted_key = message[:64]
    encrypted_message = message[64:]
    key = rsa.decrypt(encrypted_key, private_key)
    cipher = AES.new(key, AES.MODE_CFB, IV=IV)
    return cipher.decrypt(encrypted_message)

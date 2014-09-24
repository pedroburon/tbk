import base64
import binascii

from Crypto import Random
from Crypto.Hash import SHA512
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5

__all__ = ['Encryption', 'Decryption', 'InvalidMessageException']


class Encryption(object):
    def __init__(self, sender_key, recipient_key):
        self.sender_key = sender_key
        self.recipient_key = recipient_key

    def encrypt(self, message):
        key = self.get_key()
        iv = self.get_iv()

        encrypted_key = self.encrypt_key(key)

        signed_message = self.sign_message(message)
        encrypted_message = self.encrypt_message(signed_message, message, key, iv)

        return base64.b64encode(iv + encrypted_key + encrypted_message)

    def sign_message(self, message):
        hash = SHA512.new(message)
        signer = PKCS1_v1_5.new(self.sender_key)
        return signer.sign(hash)

    def encrypt_message(self, signed_message, message, key, iv):
        raw = str(signed_message) + str(message)
        block_size = AES.block_size
        pad = lambda s: s + (block_size - len(s) % block_size) * chr(block_size - len(s) % block_size)
        message_to_encrypt = pad(raw)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cipher.encrypt(message_to_encrypt)

    def encrypt_key(self, key):
        public_key = self.recipient_key.publickey()
        cipher = PKCS1_OAEP.new(public_key)
        return cipher.encrypt(key)

    def get_key(self):
        return Random.new().read(32)

    def get_iv(self):
        return Random.new().read(16)


class Decryption(object):
    def __init__(self, recipient_key, sender_key):
        self.sender_key = sender_key
        self.recipient_key = recipient_key

    def decrypt(self, message):
        raw = base64.b64decode(message)

        iv = self.get_iv(raw)
        key = self.get_key(raw)

        decrypted_message = self.get_decrypted_message(iv, key, raw)

        signature = self.get_signature(decrypted_message)
        message = self.get_message(decrypted_message)

        if self.verify(signature, message):
            return message, binascii.hexlify(signature)

        raise InvalidMessageException("Invalid message signature")

    def get_iv(self, raw):
        return raw[:16]

    def get_key(self, raw):
        recipient_key_bytes = int(self.recipient_key.publickey().n.bit_length() / 8)
        encrypted_key = raw[16:16 + recipient_key_bytes]
        cipher = PKCS1_OAEP.new(self.recipient_key)
        return cipher.decrypt(encrypted_key)

    def get_decrypted_message(self, iv, key, raw):
        recipient_key_bytes = int(self.recipient_key.publickey().n.bit_length() / 8)
        encrypted_message = raw[16 + recipient_key_bytes:]
        unpad = lambda s: s[:-ord(s[len(s) - 1:])]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(encrypted_message))

    def get_signature(self, decrypted_message):
        sender_key_bytes = int(self.sender_key.publickey().n.bit_length() / 8)
        return decrypted_message[:sender_key_bytes]

    def get_message(self, decrypted_message):
        sender_key_bytes = int(self.sender_key.publickey().n.bit_length() / 8)
        return decrypted_message[sender_key_bytes:]

    def verify(self, signature, message):
        hash = SHA512.new(message)
        verifier = PKCS1_v1_5.new(self.sender_key)

        return verifier.verify(hash, signature)


class InvalidMessageException(Exception):
    pass

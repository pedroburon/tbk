import base64

from Crypto import Random
from Crypto.Hash import SHA256
from Crypto.Cipher import AES


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
        digest = SHA256.new(message).digest()
        return self.sender_key.sign(digest, None)[0]

    def encrypt_message(self, signed_message, message, key, iv):
        raw = str(signed_message) + str(message)
        block_size = AES.block_size
        pad = lambda s: s + (block_size - len(s) % block_size) * chr(block_size - len(s) % block_size)
        message_to_encrypt = pad(raw)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cipher.encrypt(message_to_encrypt)

    def encrypt_key(self, key):
        public_key = self.recipient_key.publickey()
        return public_key.encrypt(key, None)[0]

    def get_key(self):
        return Random.new().read(32)

    def get_iv(self):
        # sagmor adds \x10\xBB\xFF\xBF\x00\x00\x00\x00\x00\x00\x00\x00\xF4\xBF to this, why?
        return Random.new().read(16)

import base64

from Crypto import Random
from Crypto.Hash import SHA512
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5


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

        return_message = base64.b64encode(iv + encrypted_key + encrypted_message)
        # return return_message
        chunks = list()
        while return_message:
            chunks.append(return_message[:60])
            return_message = return_message[60:]
        return "\n".join(chunks)

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

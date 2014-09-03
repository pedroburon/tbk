import os
import base64
from unittest import TestCase

import mock
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto import Random

from tbk.webpay.encryption import Encryption


class EncryptionTest(TestCase):
    def setUp(self):
        sender_key_path = os.path.join(os.path.dirname(__file__), 'keys', 'test_commerce.pem')
        self.sender_key = RSA.importKey(file(sender_key_path, 'r').read())
        recipient_key_path = os.path.join(os.path.dirname(__file__), 'keys', 'webpay_test.101.pem')
        self.recipient_key = RSA.importKey(file(recipient_key_path, 'r').read()).publickey()

    def test_init(self):
        encryption = Encryption(self.sender_key, self.recipient_key)

        self.assertEqual(self.sender_key, encryption.sender_key)
        self.assertEqual(self.recipient_key, encryption.recipient_key)

    @mock.patch('tbk.webpay.encryption.Encryption.get_iv')
    @mock.patch('tbk.webpay.encryption.Encryption.get_key')
    @mock.patch('tbk.webpay.encryption.Encryption.encrypt_key')
    @mock.patch('tbk.webpay.encryption.Encryption.encrypt_message')
    @mock.patch('tbk.webpay.encryption.Encryption.sign_message')
    def test_encrypt(self, sign_message, encrypt_message, encrypt_key, get_key, get_iv):
        message = "message"
        encryption = Encryption(self.sender_key, self.recipient_key)
        sender_key_bytes = self.sender_key.publickey().n.bit_length() / 8
        encrypt_message.return_value = Random.new().read(len(message))
        encrypt_key.return_value = Random.new().read(sender_key_bytes)
        get_iv.return_value = Random.new().read(16)

        encrypted_message = encryption.encrypt(message)

        data = base64.b64decode(encrypted_message)
        iv = data[0:16]
        encrypted_key = data[16:(16 + sender_key_bytes)]
        encrypted_message = data[(16 + sender_key_bytes):]

        self.assertEqual(encrypt_message.return_value, encrypted_message)
        self.assertEqual(encrypt_key.return_value, encrypted_key)
        self.assertEqual(get_iv.return_value, iv)
        encrypt_key.assert_called_once_with(get_key.return_value)
        encrypt_message.assert_called_once_with(
            sign_message.return_value, message, get_key.return_value, get_iv.return_value
        )
        sign_message.assert_called_once_with(message)

    @mock.patch('tbk.webpay.encryption.Random')
    def test_get_iv(self, Random):
        expected = Random.new.return_value.read.return_value
        encryption = Encryption(self.sender_key, self.recipient_key)

        self.assertEqual(encryption.get_iv(), expected)
        Random.new.return_value.read.assert_called_once_with(16)

    @mock.patch('tbk.webpay.encryption.Random')
    def test_get_key(self, Random):
        expected = Random.new.return_value.read.return_value
        encryption = Encryption(self.sender_key, self.recipient_key)

        self.assertEqual(encryption.get_key(), expected)
        Random.new.return_value.read.assert_called_once_with(32)

    def test_encrypt_key(self):
        key = Random.new().read(32)
        encryption = Encryption(self.sender_key, self.sender_key)

        encrypted_key = encryption.encrypt_key(key)

        self.assertEqual(
            self.sender_key.decrypt(encrypted_key),
            key
        )

    def test_sign_message(self):
        message = Random.new().read(2000)
        encryption = Encryption(self.sender_key, self.recipient_key)

        signed_message = encryption.sign_message(message)

        public_key = self.sender_key.publickey()
        digest = SHA256.new(message).digest()
        self.assertTrue(public_key.verify(digest, (signed_message,)))

    def test_encrypt_message(self):
        encryption = Encryption(self.sender_key, self.recipient_key)
        key = encryption.get_key()
        iv = encryption.get_iv()
        message = Random.new().read(10)
        signed_message = encryption.sign_message(message)

        encrypted = encryption.encrypt_message(signed_message, message, key, iv)

        cipher = AES.new(key, AES.MODE_CBC, iv)
        unpad = lambda s: s[0:-ord(s[-1])]
        decrypted = unpad(cipher.decrypt(encrypted))

        self.assertEqual(decrypted, str(signed_message) + str(message))

from __future__ import unicode_literals

import base64
from unittest import TestCase

import six
import mock
from Crypto.Hash import SHA512
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5
from Crypto import Random

from tbk.webpay.encryption import Encryption, Decryption, InvalidMessageException, DecryptionError, EncryptionError

WEBPAY_KEY = RSA.generate(4096)
WEBPAY_KEY_PUBLIC = WEBPAY_KEY.publickey()
COMMERCE_KEY = RSA.generate(2048)
COMMERCE_KEY_PUBLIC = COMMERCE_KEY.publickey()

RESPONSE_WITH_ERROR = '''
<HTML>
<BODY>
ERROR=1
TOKEN=0000000000000000000000000000000000000000000000000000000000000000
</BODY>
</HTML>
'''


class EncryptionTest(TestCase):

    def setUp(self):
        self.sender_key = COMMERCE_KEY
        self.recipient_key_private = WEBPAY_KEY
        self.recipient_key = WEBPAY_KEY_PUBLIC

    def test_init(self):
        encryption = Encryption(self.sender_key, self.recipient_key)

        self.assertEqual(self.sender_key, encryption.sender_key)
        self.assertEqual(self.recipient_key, encryption.recipient_key)

    def test_encrypt_not_binary(self):
        message = "not binary"
        encryption = Encryption(self.sender_key, self.recipient_key)

        six.assertRaisesRegex(self, EncryptionError, "Message must be binary.",
                                encryption.encrypt, message)

    @mock.patch('tbk.webpay.encryption.Encryption.get_iv')
    @mock.patch('tbk.webpay.encryption.Encryption.get_key')
    @mock.patch('tbk.webpay.encryption.Encryption.encrypt_key')
    @mock.patch('tbk.webpay.encryption.Encryption.encrypt_message')
    @mock.patch('tbk.webpay.encryption.Encryption.sign_message')
    def test_encrypt(self, sign_message, encrypt_message, encrypt_key, get_key, get_iv):
        message = Random.new().read(2000)
        encryption = Encryption(self.sender_key, self.recipient_key)
        sender_key_bytes = int(self.sender_key.publickey().n.bit_length() / 8)
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
        cipher = PKCS1_OAEP.new(self.recipient_key_private)
        encryption = Encryption(self.sender_key, self.recipient_key)

        encrypted_key = encryption.encrypt_key(key)

        self.assertEqual(
            cipher.decrypt(encrypted_key),
            key
        )

    def test_sign_message(self):
        message = Random.new().read(2000)
        encryption = Encryption(self.sender_key, self.recipient_key)

        signed_message = encryption.sign_message(message)

        public_key = self.sender_key.publickey()
        hash = SHA512.new(message)
        verifier = PKCS1_v1_5.new(public_key)
        self.assertTrue(verifier.verify(hash, signed_message))

    def test_encrypt_message(self):
        encryption = Encryption(self.sender_key, self.recipient_key)
        key = encryption.get_key()
        iv = encryption.get_iv()
        message = Random.new().read(10)
        signed_message = encryption.sign_message(message)

        encrypted = encryption.encrypt_message(signed_message, message, key, iv)

        cipher = AES.new(key, AES.MODE_CBC, iv)
        unpad = lambda s: s[:-ord(s[len(s) - 1:])]
        decrypted = unpad(cipher.decrypt(encrypted))

        self.assertEqual(decrypted, signed_message + message)


class DecryptionTest(TestCase):

    def setUp(self):
        self.sender_key_private = WEBPAY_KEY
        self.sender_key = WEBPAY_KEY_PUBLIC
        self.recipient_key = COMMERCE_KEY

    def test_init(self):
        decryption = Decryption(self.recipient_key, self.sender_key)

        self.assertEqual(self.sender_key, decryption.sender_key)
        self.assertEqual(self.recipient_key, decryption.recipient_key)

    @mock.patch('tbk.webpay.encryption.binascii.hexlify')
    @mock.patch('tbk.webpay.encryption.Decryption.get_iv')
    @mock.patch('tbk.webpay.encryption.Decryption.get_key')
    @mock.patch('tbk.webpay.encryption.Decryption.get_decrypted_message')
    @mock.patch('tbk.webpay.encryption.Decryption.get_signature')
    @mock.patch('tbk.webpay.encryption.Decryption.get_message')
    @mock.patch('tbk.webpay.encryption.Decryption.verify')
    def test_decrypt(self, verify, get_message, get_signature, get_decrypted_message, get_key, get_iv, hexlify):
        decryption = Decryption(self.recipient_key, self.sender_key)
        raw = Random.new().read(2000)
        encrypted = base64.b64encode(raw)
        message = get_message.return_value
        signature = get_signature.return_value
        hexlify_signature = hexlify.return_value
        decrypted_message = get_decrypted_message.return_value
        iv = get_iv.return_value
        key = get_key.return_value
        verify.return_value = True

        returned_message, returned_signature = decryption.decrypt(encrypted)

        self.assertEqual(message, returned_message)
        self.assertEqual(hexlify_signature, returned_signature)
        get_message.assert_called_once_with(decrypted_message)
        get_decrypted_message.assert_called_once_with(iv, key, raw)
        get_iv.assert_called_once_with(raw)
        get_key.assert_called_once_with(raw)
        get_signature.assert_called_once_with(decrypted_message)
        verify.assert_called_once_with(signature, message)
        hexlify.assert_called_once_with(signature)

    def test_decrypt_not_binary(self):
        decryption = Decryption(self.recipient_key, self.sender_key)
        message = "not binary"

        six.assertRaisesRegex(self, DecryptionError, "Message must be binary.",
                                decryption.decrypt, message)

    @mock.patch('tbk.webpay.encryption.Decryption.get_iv')
    @mock.patch('tbk.webpay.encryption.Decryption.get_key')
    @mock.patch('tbk.webpay.encryption.Decryption.get_decrypted_message')
    @mock.patch('tbk.webpay.encryption.Decryption.get_signature')
    @mock.patch('tbk.webpay.encryption.Decryption.get_message')
    @mock.patch('tbk.webpay.encryption.Decryption.verify')
    def test_decrypt_invalid(self, verify, get_message, get_signature, get_decrypted_message, get_key, get_iv):
        decryption = Decryption(self.recipient_key, self.sender_key)
        raw = Random.new().read(2000)
        encrypted = base64.b64encode(raw)
        verify.return_value = False

        six.assertRaisesRegex(self, InvalidMessageException, "Invalid message signature",
                                decryption.decrypt, encrypted)

    @mock.patch('tbk.webpay.encryption.Decryption.get_iv')
    @mock.patch('tbk.webpay.encryption.Decryption.get_key')
    @mock.patch('tbk.webpay.encryption.Decryption.get_decrypted_message')
    @mock.patch('tbk.webpay.encryption.Decryption.get_signature')
    @mock.patch('tbk.webpay.encryption.Decryption.get_message')
    @mock.patch('tbk.webpay.encryption.Decryption.verify')
    def test_decrypt_incorrect_length(self, verify, get_message, get_signature, get_decrypted_message, get_key, get_iv):
        decryption = Decryption(self.recipient_key, self.sender_key)
        get_key.side_effect = DecryptionError("Incorrect message length.")
        raw = Random.new().read(2000)
        encrypted = base64.b64encode(raw)
        verify.return_value = False

        six.assertRaisesRegex(self, DecryptionError, "Incorrect message length.",
                                decryption.decrypt, encrypted)

    def test_get_iv(self):
        decryption = Decryption(self.recipient_key, self.sender_key)
        raw = Random.new().read(2000)
        iv = raw[:16]

        self.assertEqual(iv, decryption.get_iv(raw))

    def test_get_key(self):
        decryption = Decryption(self.recipient_key, self.sender_key)
        raw = Random.new().read(16)
        key = Random.new().read(32)
        cipher = PKCS1_OAEP.new(self.recipient_key.publickey())
        encrypted_key = cipher.encrypt(key)
        raw += encrypted_key + Random.new().read(2000)

        self.assertEqual(key, decryption.get_key(raw))

    def test_get_key_incorrect_length(self):
        decryption = Decryption(self.recipient_key, self.sender_key)
        raw = base64.b64decode(RESPONSE_WITH_ERROR)

        six.assertRaisesRegex(self, DecryptionError, 'Incorrect message length.',
                                decryption.get_key, raw)

    def test_get_decrypted_message(self):
        recipient_key_bytes = int(self.recipient_key.publickey().n.bit_length() / 8)
        decryption = Decryption(self.recipient_key, self.sender_key)
        iv = Random.new().read(16)
        key = Random.new().read(32)
        encrypted_key = Random.new().read(recipient_key_bytes)
        message = ("a" * 2000).encode('utf-8')
        block_size = AES.block_size
        pad = lambda s: s + (block_size - len(s) % block_size) * chr(block_size - len(s) % block_size).encode('utf-8')
        message_to_encrypt = pad(message)
        cipher = AES.new(key, mode=AES.MODE_CBC, IV=iv)
        encrypted_message = cipher.encrypt(message_to_encrypt)

        self.assertEqual(message,
                         decryption.get_decrypted_message(iv, key, iv + encrypted_key + encrypted_message))

    def test_get_signature(self):
        sender_key_bytes = int(self.sender_key.publickey().n.bit_length() / 8)
        decryption = Decryption(self.recipient_key, self.sender_key)

        signature = Random.new().read(sender_key_bytes)
        message = Random.new().read(500)
        decrypted_message = signature + message

        self.assertEqual(signature, decryption.get_signature(decrypted_message))

    def test_get_message(self):
        sender_key_bytes = int(self.sender_key.publickey().n.bit_length() / 8)
        decryption = Decryption(self.recipient_key, self.sender_key)

        signature = Random.new().read(sender_key_bytes)
        message = Random.new().read(500)
        decrypted_message = signature + message

        self.assertEqual(message, decryption.get_message(decrypted_message))

    def test_verify_true(self):
        decryption = Decryption(self.recipient_key, self.sender_key)
        message = 'ERROR=aA321\nTOKEN=e975ffc4f0605ddf3afc299eee6aeffb59efba24769548acf58e34a89ae4e228\n'
        message = message.encode('utf-8')
        hash = SHA512.new(message)
        signer = PKCS1_v1_5.new(self.sender_key_private)
        signature = signer.sign(hash)

        self.assertTrue(decryption.verify(signature, message))

    def test_verify_false(self):
        decryption = Decryption(self.recipient_key, self.sender_key)
        wrong_message = 'ERROR=0\nTOKEN=e975ffc4f0605ddf3afc299eee6aeffb59efba24769548acf58e34a89ae4e228\n'
        message = 'ERROR=aA321\nTOKEN=e975ffc4f0605ddf3afc299eee6aeffb59efba24769548acf58e34a89ae4e228\n'
        wrong_message = wrong_message.encode('utf-8')
        message = message.encode('utf-8')
        hash = SHA512.new(wrong_message)
        signer = PKCS1_v1_5.new(self.sender_key_private)
        signature = signer.sign(hash)

        self.assertFalse(decryption.verify(signature, message))

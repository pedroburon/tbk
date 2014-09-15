import os

from .encryption import Encryption, Decryption

from Crypto.PublicKey import RSA

__all__ = ['Commerce']

KEYS_DIR = os.path.join(os.path.dirname(__file__), 'keys')
TEST_COMMERCE_KEY_PATH = os.path.join(KEYS_DIR, 'test_commerce.pem')
TEST_WEBPAY_KEY_PATH = os.path.join(KEYS_DIR, 'webpay_test.101.pem')
WEBPAY_KEY_PATH = os.path.join(KEYS_DIR, 'webpay.101.pem')


class Commerce(object):
    TEST_COMMERCE_KEY = open(TEST_COMMERCE_KEY_PATH, 'r').read()
    TEST_COMMERCE_ID = "597026007976"

    webpay_key_id = 101

    def __init__(self, id=None, key=None, testing=False):
        self.testing = testing
        self.id = self.__get_id(id)
        self.key = self.__get_key(key)

    @staticmethod
    def create_commerce():
        """
        Creates commerce from environment variables.
        """
        commerce_id = os.getenv('TBK_COMMERCE_ID')
        commerce_key = os.getenv('TBK_COMMERCE_KEY')
        commerce_testing = os.getenv('TBK_COMMERCE_TESTING') == 'True'

        if not commerce_testing:
            if commerce_id is None:
                raise ValueError("create_commerce needs TBK_COMMERCE_ID environment variable")
            if commerce_key is None:
                raise ValueError("create_commerce needs TBK_COMMERCE_KEY environment variable")

        return Commerce(
            id=commerce_id or Commerce.TEST_COMMERCE_ID,
            key=commerce_key,
            testing=commerce_testing
        )

    def __get_key(self, key):
        if not key:
            if self.testing:
                return self.TEST_COMMERCE_KEY
            raise TypeError("Commerce needs a key")
        return key

    def __get_id(self, id):
        if not id:
            if self.testing:
                return self.TEST_COMMERCE_ID
            raise TypeError("Commerce needs an id")
        return id

    def webpay_decrypt(self, encrypted):
        commerce_key = self.get_commerce_key()
        webpay_key = self.get_webpay_key()
        decryption = Decryption(commerce_key, webpay_key)
        decrypted = decryption.decrypt(encrypted)
        return decrypted

    def webpay_encrypt(self, decrypted):
        commerce_key = self.get_commerce_key()
        webpay_key = self.get_webpay_key()
        encryption = Encryption(commerce_key, webpay_key)
        return encryption.encrypt(decrypted)

    def get_webpay_key(self):
        path = TEST_WEBPAY_KEY_PATH if self.testing else WEBPAY_KEY_PATH
        with open(path, 'r') as webpay_key:
            return RSA.importKey(webpay_key.read())

    def get_commerce_key(self):
        return RSA.importKey(self.key)

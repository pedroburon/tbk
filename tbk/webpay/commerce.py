import os

from .config import Config
from .encryption import Encryption

from Crypto.PublicKey import RSA

__all__ = ['Commerce']

KEYS_DIR = os.path.join(os.path.dirname(__file__), 'keys')
TEST_COMMERCE_KEY_PATH = os.path.join(KEYS_DIR, 'test_commerce.pem')
TEST_WEBPAY_KEY_PATH = os.path.join(KEYS_DIR, 'webpay_test.101.pem')
WEBPAY_KEY_PATH = os.path.join(KEYS_DIR, 'webpay.101.pem')


class Commerce(object):
    TEST_COMMERCE_KEY = open(TEST_COMMERCE_KEY_PATH, 'r').read()

    webpay_key_id = "101"

    def __init__(self, id, key, testing=False):
        self.id = id
        self.key = key
        self.testing = testing

    @staticmethod
    def create_commerce(config=None):
        config = config or Config()
        return Commerce(config.commerce_id,
                        config.commerce_key,
                        config.environment == config.DEVELOPMENT)

    def webpay_decrypt(self, encrypted):
        return {}

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


from .config import Config

__all__ = ['Commerce']


class Commerce(object):
    TEST_COMMERCE_KEY = 'akey'

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
        return ''

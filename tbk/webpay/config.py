import os

__all__ = ['Config', 'TBK_VERSION_KCC']

TBK_VERSION_KCC = '6.0'


class Config(object):
    PRODUCTION = 'production'
    DEVELOPMENT = 'development'

    commerce_id = None
    commerce_key = None
    environment = None

    def __init__(self, commerce_id=None, commerce_key=None, environment=None):
        self.commerce_id = commerce_id or os.getenv('TBK_COMMERCE_ID')
        self.commerce_key = commerce_key or os.getenv('TBK_COMMERCE_KEY')
        self.environment = environment or \
            os.getenv('TBK_COMMERCE_ENVIRONMENT') or \
            self.PRODUCTION

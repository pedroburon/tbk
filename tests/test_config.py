from unittest import TestCase

import mock

from tbk.webpay import Config


class ConfigTest(TestCase):
    def test_commerce_id_none_by_default(self):
        '''
        commerce_id should be None by default
        '''
        config = Config()
        self.assertIsNone(config.commerce_id)

    def test_commerce_id_by_kwarg(self):
        '''
        commerce_id should be configured by keyword arg
        '''
        config = Config(commerce_id='54321')
        self.assertEqual('54321', config.commerce_id)

    def test_commerce_id_from_env(self):
        '''
        should read it's default value from the environment
        '''
        with mock.patch('os.getenv') as getenv:
            getenv.return_value = '12345'
            config = Config()
            self.assertEqual(config.commerce_id, '12345')
            getenv.assert_any_call('TBK_COMMERCE_ID')

    def test_commerce_key_none_by_default(self):
        '''
        commerce_id should be nil by default
        '''
        config = Config()
        self.assertIsNone(config.commerce_key)

    def test_commerce_key_by_kwarg(self):
        '''
        commerce_key should be configured by keyword arg
        '''
        config = Config(commerce_key='PKEY')
        self.assertEqual('PKEY', config.commerce_key)

    def test_commerce_key_from_env(self):
        '''
        commerce_key should read it's default value from the environment
        '''
        with mock.patch('os.getenv') as getenv:
            getenv.return_value = 'PKEY'
            config = Config()
            self.assertEqual(config.commerce_key, 'PKEY')
            getenv.assert_any_call('TBK_COMMERCE_KEY')

    def test_production_by_default(self):
        '''
        environment should be production by default
        '''
        config = Config()
        self.assertEqual(Config.PRODUCTION, config.environment)

    def test_environment_by_kwarg(self):
        '''
        environment should be configured by keyword arg
        '''
        config = Config(environment=Config.DEVELOPMENT)
        self.assertEqual(Config.DEVELOPMENT, config.environment)

    def test_environment_from_env(self):
        '''
        commerce_key should read it's default value from the environment
        '''
        with mock.patch('os.getenv') as getenv:
            getenv.return_value = Config.DEVELOPMENT
            config = Config()
            self.assertEqual(config.environment, Config.DEVELOPMENT)
            getenv.assert_any_call('TBK_COMMERCE_ENVIRONMENT')

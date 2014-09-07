import os
from unittest import TestCase

import mock
from Crypto.PublicKey import RSA

from tbk.webpay import Commerce


class CommerceTest(TestCase):
    def test_called_with_all_arguments(self):
        """
        init Commerce can be done with all it's arguments
        """
        commerce = Commerce(id="12345", key=Commerce.TEST_COMMERCE_KEY,
                            testing=True)
        self.assertEqual(commerce.id, "12345")
        self.assertEqual(commerce.key, Commerce.TEST_COMMERCE_KEY)
        self.assertTrue(commerce.testing)
        self.assertEqual(101, commerce.webpay_key_id)

    def test_no_id_given(self):
        """
        init Commerce raises an exception if no id is given
        """
        self.assertRaises(TypeError, Commerce, key=Commerce.TEST_COMMERCE_KEY)

    def test_no_key_given(self):
        """
        init Commerce raises an exception if no key is given
        """
        self.assertRaises(TypeError, Commerce, id="12345")

    def test_no_testing_given(self):
        """
        init Commerce set testing to False
        """
        commerce = Commerce(id="12345", key=Commerce.TEST_COMMERCE_KEY)
        self.assertFalse(commerce.testing)

    @mock.patch('tbk.webpay.commerce.Config')
    def test_create_commerce(self, Config):
        """
        Create commerce with default config
        """
        config = mock.Mock()
        Config.return_value = config
        commerce = Commerce.create_commerce()

        self.assertEqual(commerce.id, config.commerce_id)
        self.assertEqual(commerce.key, config.commerce_key)
        self.assertEqual(commerce.testing,
                         config.environment == config.DEVELOPMENT)

        Config.assert_called_once_with()

    @mock.patch('tbk.webpay.commerce.Config')
    def test_create_commerce_with_config(self, Config):
        '''
        Create commerce with a Config
        '''
        config = mock.Mock()
        commerce = Commerce.create_commerce(config)

        self.assertEqual(commerce.id, config.commerce_id)
        self.assertEqual(commerce.key, config.commerce_key)

        self.assertFalse(Config.called)

    @mock.patch('tbk.webpay.commerce.Commerce.get_commerce_key')
    @mock.patch('tbk.webpay.commerce.Commerce.get_webpay_key')
    @mock.patch('tbk.webpay.commerce.Encryption')
    def test_webpay_encrypt(self, Encryption, get_webpay_key, get_commerce_key):
        commerce = Commerce.create_commerce()
        message = "decrypted"

        result = commerce.webpay_encrypt(message)

        Encryption.assert_called_once_with(get_commerce_key.return_value,
                                           get_webpay_key.return_value)
        encryption = Encryption.return_value
        encryption.encrypt.assert_called_once_with(message)
        get_webpay_key.assert_called_once_with()
        get_commerce_key.assert_called_once_with()
        self.assertEqual(result, encryption.encrypt.return_value)

    @mock.patch('tbk.webpay.commerce.Commerce.get_commerce_key')
    @mock.patch('tbk.webpay.commerce.Commerce.get_webpay_key')
    @mock.patch('tbk.webpay.commerce.Decryption')
    def test_webpay_decrypt(self, Decryption, get_webpay_key, get_commerce_key):
        commerce = Commerce.create_commerce()
        message = "encrypted"

        result = commerce.webpay_decrypt(message)

        Decryption.assert_called_once_with(get_commerce_key.return_value,
                                           get_webpay_key.return_value)
        decryption = Decryption.return_value
        decryption.decrypt.assert_called_once_with(message)
        get_webpay_key.assert_called_once_with()
        get_commerce_key.assert_called_once_with()
        self.assertEqual(result, decryption.decrypt.return_value)

    def test_get_commerce_key(self):
        testing_path = os.path.join(os.path.dirname(__file__), 'keys', 'test_commerce.pem')
        with open(testing_path, 'r') as testing_file:
            commerce = Commerce.create_commerce()
            commerce.key = Commerce.TEST_COMMERCE_KEY

            expected_key = RSA.importKey(testing_file.read())
            self.assertEqual(expected_key, commerce.get_commerce_key())

    def test_get_webpay_key_testing(self):
        webpay_testing_path = os.path.join(os.path.dirname(__file__), 'keys', 'webpay_test.101.pem')
        with open(webpay_testing_path, 'r') as testing_file:
            commerce = Commerce.create_commerce()
            commerce.testing = True

            expected_key = RSA.importKey(testing_file.read())
            key = commerce.get_webpay_key()

            self.assertEqual(expected_key, key)

    def test_get_webpay_key(self):
        webpay_path = os.path.join(os.path.dirname(__file__), 'keys', 'webpay.101.pem')
        with open(webpay_path, 'r') as testing_file:
            commerce = Commerce.create_commerce()
            commerce.testing = False

            expected_key = RSA.importKey(testing_file.read())
            key = commerce.get_webpay_key()

            self.assertEqual(expected_key, key)

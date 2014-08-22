from unittest import TestCase

import mock

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

    def test_webpay_decrypt(self):
        commerce = Commerce.create_commerce()

        result = commerce.webpay_decrypt("encrypted")
        self.assertIsInstance(result, dict)

    def test_webpay_encrypt(self):
        commerce = Commerce.create_commerce()

        commerce.webpay_encrypt("decrypted")

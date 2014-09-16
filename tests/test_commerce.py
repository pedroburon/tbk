import os
from unittest import TestCase

import mock
from Crypto.PublicKey import RSA

from tbk.webpay.commerce import Commerce


class CommerceTest(TestCase):
    def test_called_with_all_arguments(self):
        """
        init Commerce can be done with all it's arguments
        """
        commerce = Commerce(id="12345", key="commerce_key",
                            testing=True)
        self.assertEqual(commerce.id, "12345")
        self.assertEqual(commerce.key, "commerce_key")
        self.assertTrue(commerce.testing)
        self.assertEqual(101, commerce.webpay_key_id)

    def test_no_id_given(self):
        """
        init Commerce raises an exception if no id is given
        """
        self.assertRaisesRegexp(TypeError, "Commerce needs an id",
                                Commerce, key=Commerce.TEST_COMMERCE_KEY)

    def test_no_key_given_no_testing(self):
        """
        init Commerce raises an exception if no key is given and testing is False
        """
        self.assertRaisesRegexp(TypeError, "Commerce needs a key",
                                Commerce, id="12345", testing=False)

    def test_no_key_given_testing(self):
        """
        init Commerce sets test_commerce key when no key is given and testings is True
        """
        commerce = Commerce(id="12345", testing=True)

        self.assertEqual(commerce.key, Commerce.TEST_COMMERCE_KEY)

    def test_no_id_given_testing(self):
        """
        init Commerce sets test_commerce key when no id is given and testings is True
        """
        commerce = Commerce(key="commerce_key", testing=True)

        self.assertEqual(commerce.id, Commerce.TEST_COMMERCE_ID)

    def test_no_testing_given(self):
        """
        init Commerce set testing to False
        """
        commerce = Commerce(id="12345", key=Commerce.TEST_COMMERCE_KEY)
        self.assertFalse(commerce.testing)

    @mock.patch('tbk.webpay.commerce.os.environ', {
        'TBK_COMMERCE_ID': '54321',
        'TBK_COMMERCE_TESTING': 'True'
    })
    def test_create_commerce_with_commerce_id(self):
        """
        create_commerce create a commerce with environ TBK_COMMERCE_ID and TBK_COMMERCE_TESTING=True
        """
        commerce = Commerce.create_commerce()
        self.assertEqual(commerce.id, '54321')
        self.assertTrue(commerce.testing)
        self.assertEqual(commerce.key, commerce.TEST_COMMERCE_KEY)

    @mock.patch.dict('tbk.webpay.commerce.os.environ', {
        'TBK_COMMERCE_TESTING': 'True'
    })
    def test_create_commerce_with_no_commerce_id(self):
        """
        create_commerce create a commerce with environ TBK_COMMERCE_TESTING=True
        """
        commerce = Commerce.create_commerce()
        self.assertEqual(commerce.id, commerce.TEST_COMMERCE_ID)
        self.assertTrue(commerce.testing)
        self.assertEqual(commerce.key, commerce.TEST_COMMERCE_KEY)

    @mock.patch.dict('tbk.webpay.commerce.os.environ', {})
    def test_create_commerce_with_no_commerce_id_and_no_testing(self):
        """
        create_commerce create a commerce with environ TBK_COMMERCE_TESTING=False
        """
        self.assertRaisesRegexp(ValueError, "create_commerce needs TBK_COMMERCE_ID environment variable",
                                Commerce.create_commerce)

    @mock.patch.dict('tbk.webpay.commerce.os.environ', {
        'TBK_COMMERCE_ID': '1234',
        'TBK_COMMERCE_TESTING': 'False'
    })
    def test_create_commerce_with_no_commerce_key_and_no_testing(self):
        """
        create_commerce create a commerce with environ TBK_COMMERCE_TESTING=False
        """
        self.assertRaisesRegexp(ValueError, "create_commerce needs TBK_COMMERCE_KEY environment variable",
                                Commerce.create_commerce)

    @mock.patch('tbk.webpay.commerce.Commerce.get_commerce_key')
    @mock.patch('tbk.webpay.commerce.Commerce.get_webpay_key')
    @mock.patch('tbk.webpay.commerce.Encryption')
    def test_webpay_encrypt(self, Encryption, get_webpay_key, get_commerce_key):
        commerce = Commerce(id="12345", testing=True)
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
        commerce = Commerce(id=12345, testing=True)
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
            commerce = Commerce(id=12345, testing=True)
            commerce.key = Commerce.TEST_COMMERCE_KEY

            expected_key = RSA.importKey(testing_file.read())
            self.assertEqual(expected_key, commerce.get_commerce_key())

    def test_get_webpay_key_testing(self):
        webpay_testing_path = os.path.join(os.path.dirname(__file__), 'keys', 'webpay_test.101.pem')
        with open(webpay_testing_path, 'r') as testing_file:
            commerce = Commerce(id=12345, testing=True)
            commerce.testing = True

            expected_key = RSA.importKey(testing_file.read())
            key = commerce.get_webpay_key()

            self.assertEqual(expected_key, key)

    def test_get_webpay_key(self):
        webpay_path = os.path.join(os.path.dirname(__file__), 'keys', 'webpay.101.pem')
        with open(webpay_path, 'r') as testing_file:
            commerce = Commerce(id=12345, testing=True)
            commerce.testing = False

            expected_key = RSA.importKey(testing_file.read())
            key = commerce.get_webpay_key()

            self.assertEqual(expected_key, key)

    def test_get_public_key(self):
        private_key = RSA.generate(2048)
        commerce_key = private_key.exportKey()
        commerce = Commerce(id="12345", key=commerce_key)

        self.assertEqual(private_key.publickey().exportKey(), commerce.get_public_key())

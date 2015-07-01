from unittest import TestCase
from collections import OrderedDict

from tbk.webpay import Commerce
from tbk.webpay.params import Params

import mock
import hashlib


class ParamsTest(TestCase):
    def setUp(self):
        self.commerce = mock.Mock(spec=Commerce)
        self.commerce.id = Commerce.TEST_COMMERCE_ID

    def test_initialize(self):
        params = Params(commerce=self.commerce)

        self.assertTrue(issubclass(Params, OrderedDict))
        self.assertIsInstance(params, Params)
        self.assertEqual(self.commerce, params.commerce)

    def test_initialize_with_args(self):
        kwargs = OrderedDict()
        kwargs['foo'] = 'bar'
        kwargs['bar'] = 'baz'
        params = Params(commerce=self.commerce)
        params['foo'] = 'bar'
        params['bar'] = 'baz'        

        self.assertEqual(self.commerce, params.commerce)
        self.assertEqual(kwargs, params)

    def test_initialize_without_commerce(self):
        with self.assertRaisesRegexp(TypeError, "Must create Params with Commerce instance."):
            Params()

    def test_validate(self):
        params = Params(commerce=self.commerce)

        params.validate()

    def test_get_raw(self):
        hash = hashlib.new('md5')
        hash.update(b'foo=bar&bar=baz')
        hash.update(self.commerce.id.encode('utf-8'))
        hash.update(b'webpay')        
        params = Params(commerce=self.commerce)
        params['foo'] = 'bar'
        params['bar'] = 'baz'
        expected = 'foo=bar#bar=baz'

        self.assertEqual(expected, params.get_raw())

    def test_get_encrypted(self):
        hash = hashlib.new('md5')
        hash.update(b'foo=bar&bar=baz')
        hash.update(self.commerce.id.encode('utf-8'))
        hash.update(b'webpay')        
        params = Params(commerce=self.commerce)
        params['foo'] = 'bar'
        params['bar'] = 'baz'
        raw_params = 'foo=bar#bar=baz'

        self.commerce.webpay_encrypt.called_once_with(raw_params)

        self.assertEqual(self.commerce.webpay_encrypt.return_value, params.get_encrypted())

    def test_use_clean_foo(self):
        hash = hashlib.new('md5')
        hash.update(b'foo=baz&bar=baz')
        hash.update(self.commerce.id.encode('utf-8'))
        hash.update(b'webpay')        
        raw_params = 'foo=baz#bar=baz'
        mock_function = mock.Mock()

        class SubParams(Params):
            def clean_foo(self, value):
                mock_function(value)
                return 'baz'

        params = SubParams(commerce=self.commerce)
        params['foo'] = 'bar'
        params['bar'] = 'baz'

        self.assertEqual(raw_params, params.get_raw())
        mock_function.assert_called_once_with('bar')

    def test_dont_use_foo(self):
        hash = hashlib.new('md5')
        hash.update(b'bar=baz')
        hash.update(self.commerce.id.encode('utf-8'))
        hash.update(b'webpay')        
        raw_params = 'bar=baz'
        mock_function = mock.Mock()

        class SubParams(Params):
            def clean_foo(self, value):
                mock_function(value)
                raise SubParams.DontUseParam

        params = SubParams(commerce=self.commerce)
        params['foo'] = 'bar'
        params['bar'] = 'baz'

        self.assertEqual(raw_params, params.get_raw())
        mock_function.assert_called_once_with('bar')

    def test_iterate_over_fields(self):        
        raw_params = 'bar=baz'
        mock_function = mock.Mock()

        class SubParams(Params):
            fields = ['bar']

        params = SubParams(commerce=self.commerce)
        params['foo'] = 'bar'
        params['bar'] = 'baz'

        self.assertEqual(raw_params, params.get_raw())

    def test_validate_with_fields(self):
        class SubParams(Params):
            fields = ['foo']

        params = SubParams(commerce=self.commerce)

        with self.assertRaisesRegexp(SubParams.KeyExpected, 'foo'):
            params.validate()

    def test_clean_TBK_MAC(self):
        hash = hashlib.new('md5')
        hash.update(b'bar=baz')
        hash.update(self.commerce.id.encode('utf-8'))
        hash.update(b'webpay')

        params = Params(commerce=self.commerce)
        params['bar'] = 'baz'

        self.assertEqual(hash.hexdigest(), params.clean_TBK_MAC(None))

    def test_field_not_in_keys(self):
        class SubParams(Params):
            fields = ('foo',)

        params = SubParams(commerce=self.commerce)

        with self.assertRaisesRegexp(SubParams.KeyExpected, 'foo'):
            params.get_raw()

    def test_field_not_in_keys_but_clean(self):
        class SubParams(Params):
            fields = ('foo', 'bar')

            def clean_foo(self, value):
                return 'bar'

        params = SubParams(commerce=self.commerce)
        params['bar'] = 'baz'

        self.assertEqual('foo=bar#bar=baz', params.get_raw())

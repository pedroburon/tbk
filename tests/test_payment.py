import os
import sys
from decimal import Decimal, ROUND_DOWN
from unittest import TestCase

import six
import mock

from tbk.webpay import TBK_VERSION_KCC
from tbk.webpay.payment import Payment, PaymentError
from tbk.webpay.encryption import DecryptionError

RESPONSE_WITH_ERROR = '''
<HTML>
<BODY>
ERROR=1
TOKEN=0000000000000000000000000000000000000000000000000000000000000000
</BODY>
</HTML>
'''


class PaymentTest(TestCase):

    def setUp(self):
        self.payment_kwargs = {
            'request_ip': '123.123.123.123',
            'commerce': mock.Mock(),
            'success_url': 'http://localhost:8080/webpay/success/',
            'confirmation_url': 'http://127.0.0.1:8080/webpay/confirmation/',
            'failure_url': 'http://localhost:8080/webpay/failure/',
            'session_id': 'SOME_SESSION_VALUE',
            'amount': '123456',
            'order_id': "1",
        }

    def test_initialize_with_all_args(self):
        """
        Create Payment with all it's args
        """
        amount = Decimal(self.payment_kwargs['amount']).quantize(Decimal('.01'), rounding=ROUND_DOWN)
        payment = Payment(**self.payment_kwargs)
        self.assertEqual(payment.commerce, self.payment_kwargs['commerce'])
        self.assertEqual(payment.request_ip, self.payment_kwargs['request_ip'])
        self.assertEqual(payment.amount, amount)
        self.assertEqual(payment.order_id, self.payment_kwargs['order_id'])
        self.assertEqual(
            payment.success_url, self.payment_kwargs['success_url'])
        self.assertEqual(payment.confirmation_url, self.payment_kwargs['confirmation_url'])
        self.assertEqual(payment.session_id, self.payment_kwargs['session_id'])
        self.assertEqual(
            payment.failure_url, self.payment_kwargs['failure_url'])

    @mock.patch('tbk.webpay.payment.Commerce.create_commerce')
    def test_initialize_without_commerce(self, create_commerce):
        """
        Create Payment and it uses default commerce from create_commerce
        """
        del self.payment_kwargs['commerce']
        payment = Payment(**self.payment_kwargs)
        self.assertEqual(payment.commerce, create_commerce.return_value)
        create_commerce.assert_called_once_with()

    def test_initialize_without_failure_url(self):
        """
        Create Payment and it sets failure_url as success_url
        """
        del self.payment_kwargs['failure_url']
        payment = Payment(**self.payment_kwargs)

        self.assertEqual(
            payment.failure_url, self.payment_kwargs['success_url'])

    def test_initialize_without_session_id(self):
        """
        Create Payment and it sets session_id to None
        """
        del self.payment_kwargs['session_id']
        payment = Payment(**self.payment_kwargs)

        self.assertIsNone(payment.session_id)

    def test_initialize_with_float_amount(self):
        """
        Creating Payment with float amount convert it to Decimal
        """
        self.payment_kwargs['amount'] = 1234.56
        payment = Payment(**self.payment_kwargs)

        self.assertEqual(Decimal("1234.56"), payment.amount)

    def test_quantize_amount(self):
        """
        Creating Payment with float amount convert it to Decimal quantized
        """
        self.payment_kwargs['amount'] = 1234.567
        payment = Payment(**self.payment_kwargs)

        self.assertEqual(Decimal("1234.57"), payment.amount)

    @mock.patch('tbk.webpay.payment.Payment.get_process_url')
    @mock.patch('tbk.webpay.payment.Payment.token')
    def test_redirect_url(self, token, process_url):
        """
        payment.redirect_url must return the url to redirect using process_url and token methods.
        """
        payment = Payment(**self.payment_kwargs)
        redirect_url = "%(process_url)s?TBK_VERSION_KCC=%(tbk_version)s&" \
            "TBK_TOKEN=%(token)s"
        expected = redirect_url % {
            'process_url': process_url.return_value,
            'tbk_version': TBK_VERSION_KCC,
            'token': token
        }
        self.assertEqual(expected, payment.redirect_url)

    def test_get_process_url_development(self):
        """
        payment.get_process_url on dev must return https://certificacion.webpay.cl:6443/filtroUnificado/bp_revision.cgi
        """
        commerce = mock.Mock()
        commerce.testing = True
        self.payment_kwargs['commerce'] = commerce
        payment = Payment(**self.payment_kwargs)

        self.assertEqual(
            "https://certificacion.webpay.cl:6443/filtroUnificado/bp_revision.cgi",
            payment.get_process_url()
        )

    def test_get_process_url_production(self):
        """
        payment.get_process_url on prod must return https://webpay.transbank.cl:443/filtroUnificado/bp_revision.cgi
        """
        commerce = mock.Mock()
        commerce.testing = False
        self.payment_kwargs['commerce'] = commerce
        payment = Payment(**self.payment_kwargs)

        self.assertEqual(
            "https://webpay.transbank.cl:443/filtroUnificado/bp_revision.cgi",
            payment.get_process_url()
        )

    @mock.patch('tbk.webpay.payment.Payment.fetch_token')
    @mock.patch('tbk.webpay.payment.logger')
    def test_token_not_created(self, logger, fetch_token):
        """
        payment.token must return a token from fetch_token and log
        """
        payment = Payment(**self.payment_kwargs)

        self.assertEqual(
            fetch_token.return_value,
            payment.token
        )
        logger.payment.assert_called_once_with(payment)

    @mock.patch('tbk.webpay.payment.Payment.fetch_token')
    @mock.patch('tbk.webpay.payment.logger')
    def test_token_created(self, logger, fetch_token):
        """
        payment.token must return a token already fetched by fetch_token and dont log
        """
        payment = Payment(**self.payment_kwargs)
        token = payment.token

        fetch_token.reset_mock()
        logger.reset_mock()

        self.assertEqual(
            token,
            payment.token
        )
        self.assertFalse(fetch_token.called)
        self.assertFalse(logger.payment.called)

    @mock.patch('tbk.webpay.payment.requests')
    @mock.patch('tbk.webpay.payment.Payment.get_validation_url')
    @mock.patch('tbk.webpay.payment.Payment.params')
    def test_fetch_token(self, params, get_validation_url, requests):
        """
        payment.fetch_token must post data to get_validation_url and get token from response
        """
        python_version = "%d.%d" % (sys.version_info.major, sys.version_info.minor)
        user_agent = "TBK/%(TBK_VERSION_KCC)s (Python/%(PYTHON_VERSION)s)" % {
            'TBK_VERSION_KCC': TBK_VERSION_KCC,
            'PYTHON_VERSION': python_version
        }
        commerce = self.payment_kwargs['commerce']
        payment = Payment(**self.payment_kwargs)
        response = requests.post.return_value
        response.status_code = 200
        response.is_redirect = False
        decrypted = 'ERROR=0\nTOKEN=e975ffc4f0605ddf3afc299eee6aeffb59efba24769548acf58e34a89ae4e228\n'
        signature = "signature" * 20
        commerce.webpay_decrypt.return_value = decrypted, signature

        token = payment.fetch_token()

        requests.post.assert_called_once_with(
            get_validation_url.return_value,
            data={
                'TBK_VERSION_KCC': TBK_VERSION_KCC,
                'TBK_CODIGO_COMERCIO': commerce.id,
                'TBK_KEY_ID': commerce.webpay_key_id,
                'TBK_PARAM': params
            },
            headers={
                'User-Agent': user_agent
            },
            allow_redirects=False
        )
        commerce.webpay_decrypt.assert_called_once_with(response.content)

        self.assertEqual(token, 'e975ffc4f0605ddf3afc299eee6aeffb59efba24769548acf58e34a89ae4e228')

    @mock.patch('tbk.webpay.payment.requests')
    @mock.patch('tbk.webpay.payment.Payment.get_validation_url')
    @mock.patch('tbk.webpay.payment.Payment.params')
    def test_fetch_token_with_redirect(self, params, get_validation_url, requests):
        """
        payment.fetch_token must post data to get_validation_url and get token from response after redirect.
        """
        commerce = self.payment_kwargs['commerce']
        payment = Payment(**self.payment_kwargs)
        response1 = mock.Mock()
        response1.is_redirect = True
        response1.status_code = 302
        response2 = mock.Mock()
        response2.is_redirect = False
        response2.status_code = 200
        requests.post.side_effect = [response1, response2]
        decrypted = 'ERROR=0\nTOKEN=e975ffc4f0605ddf3afc299eee6aeffb59efba24769548acf58e34a89ae4e228\n'
        signature = "signature" * 20
        commerce.webpay_decrypt.return_value = decrypted, signature

        token = payment.fetch_token()

        commerce.webpay_decrypt.assert_called_once_with(response2.content)

        self.assertEqual(token, 'e975ffc4f0605ddf3afc299eee6aeffb59efba24769548acf58e34a89ae4e228')

    @mock.patch('tbk.webpay.payment.requests')
    @mock.patch('tbk.webpay.payment.Payment.get_validation_url')
    @mock.patch('tbk.webpay.payment.Payment.params')
    def test_fetch_token_not_ok(self, params, get_validation_url, requests):
        """
        payment.fetch_token must post data to get_validation_url and fail when status_code is not 200
        """
        payment = Payment(**self.payment_kwargs)
        response = requests.post.return_value
        response.status_code = 500
        response.is_redirect = False

        six.assertRaisesRegex(self, 
            PaymentError, "Payment token generation failed",
            payment.fetch_token
        )

    @mock.patch('tbk.webpay.payment.requests')
    @mock.patch('tbk.webpay.payment.Payment.get_validation_url')
    @mock.patch('tbk.webpay.payment.Payment.params')
    def test_fetch_token_with_error(self, params, get_validation_url, requests):
        """
        payment.fetch_token must post data to get_validation_url and fail with ERROR code
        """
        payment = Payment(**self.payment_kwargs)
        response = requests.post.return_value
        response.is_redirect = False
        response.status_code = 200
        commerce = self.payment_kwargs['commerce']
        decrypted = 'ERROR=aA321\nTOKEN=e975ffc4f0605ddf3afc299eee6aeffb59efba24769548acf58e34a89ae4e228\n'
        signature = "signature" * 20
        commerce.webpay_decrypt.return_value = decrypted, signature

        six.assertRaisesRegex(self, 
            PaymentError, "Payment token generation failed. ERROR=aA321",
            payment.fetch_token
        )

    @mock.patch('tbk.webpay.payment.requests')
    @mock.patch('tbk.webpay.payment.Payment.get_validation_url')
    @mock.patch('tbk.webpay.payment.Payment.params')
    def test_fetch_token_with_unapproved_key(self, params, get_validation_url, requests):
        """
        payment.fetch_token must post data to get_validation_url and fail when cannot decrypt with ERROR code
        """
        payment = Payment(**self.payment_kwargs)
        response = requests.post.return_value
        response.is_redirect = False
        response.status_code = 200
        response.content = RESPONSE_WITH_ERROR
        commerce = self.payment_kwargs['commerce']
        commerce.webpay_decrypt.side_effect = DecryptionError

        six.assertRaisesRegex(self, 
            PaymentError, "Payment token generation failed. ERROR=1",
            payment.fetch_token
        )

    @mock.patch('tbk.webpay.payment.get_token_from_body')
    @mock.patch('tbk.webpay.payment.requests')
    @mock.patch('tbk.webpay.payment.Payment.get_validation_url')
    @mock.patch('tbk.webpay.payment.Payment.params')
    def test_fetch_token_with_suspicios_message(self, params, get_validation_url, requests, get_token_from_body):
        """
        payment.fetch_token must post data to get_validation_url and fail when cannot decrypt with ERROR code
        """
        payment = Payment(**self.payment_kwargs)
        response = requests.post.return_value
        response.is_redirect = False
        response.status_code = 200
        response.content = "I'm suspicious..."
        commerce = self.payment_kwargs['commerce']
        commerce.webpay_decrypt.side_effect = DecryptionError
        get_token_from_body.return_value = response.content

        six.assertRaisesRegex(self, 
            PaymentError, "Suspicious message from server: " + get_token_from_body.return_value,
            payment.fetch_token
        )

    def test_get_validation_url_production(self):
        """
        payment.get_validation_url on prod. must returns
        https://webpay.transbank.cl:443/filtroUnificado/bp_validacion.cgi
        """
        commerce = mock.Mock()
        commerce.testing = False
        self.payment_kwargs['commerce'] = commerce
        payment = Payment(**self.payment_kwargs)

        self.assertEqual(
            "https://webpay.transbank.cl:443/filtroUnificado/bp_validacion.cgi",
            payment.get_validation_url()
        )

    def test_get_validation_url_development(self):
        """
        payment.get_validation_url on dev. must returns
        https://certificacion.webpay.cl:6443/filtroUnificado/bp_validacion.cgi
        """
        commerce = mock.Mock()
        commerce.testing = True
        self.payment_kwargs['commerce'] = commerce
        payment = Payment(**self.payment_kwargs)

        self.assertEqual(
            "https://certificacion.webpay.cl:6443/filtroUnificado/bp_validacion.cgi",
            payment.get_validation_url()
        )

    @mock.patch('tbk.webpay.payment.Payment.get_raw_params')
    @mock.patch('tbk.webpay.payment.Payment.verify')
    def test_params_not_created(self, verify, get_raw_params):
        """
        payment.params must verify and returns encrypted get_raw_params
        """
        commerce = self.payment_kwargs['commerce']
        payment = Payment(**self.payment_kwargs)

        result = payment.params

        verify.assert_called_once_with()
        commerce.webpay_encrypt.assert_called_once_with(get_raw_params.return_value)
        self.assertEqual(result, commerce.webpay_encrypt.return_value)
        get_raw_params.assert_called_once_with()

    @mock.patch('tbk.webpay.payment.Payment.get_raw_params')
    @mock.patch('tbk.webpay.payment.Payment.verify')
    def test_params_created(self, verify, get_raw_params):
        """
        payment.params must returns the already verified and encrypted get_raw_params
        """
        commerce = self.payment_kwargs['commerce']
        payment = Payment(**self.payment_kwargs)
        result = payment.params

        verify.reset_mock()
        commerce.webpay_encrypt.reset_mock()
        get_raw_params.reset_mock()

        self.assertEqual(payment.params, result)
        self.assertFalse(verify.called)
        self.assertFalse(commerce.webpay_encrypt.called)
        self.assertFalse(get_raw_params.called)

    @mock.patch('tbk.webpay.payment.Payment.get_raw_params')
    @mock.patch('tbk.webpay.payment.Payment.verify')
    def test_params_doesnt_verify(self, verify, get_raw_params):
        """
        payment.params must fail with PaymentError when verify fail
        """
        payment = Payment(**self.payment_kwargs)
        verify.side_effect = PaymentError

        with self.assertRaises(PaymentError):
            payment.params
        verify.assert_called_once_with()

    @mock.patch('tbk.webpay.payment.hashlib')
    def test_get_raw_params(self, hashlib):
        """
        payment.get_raw_params returns params as seen on raw_params.txt
        """
        h = hashlib.new.return_value
        h.hexdigest.return_value = "8455b5720ff48c0efae649a42b6d1aa2"
        commerce = self.payment_kwargs['commerce']
        commerce.id = "1234567890"
        commerce.webpay_key_id = '101'
        payment = Payment(**self.payment_kwargs)
        payment._transaction_id = 123456789
        get_raw_params_file_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'raw_params.txt')
        with open(get_raw_params_file_path, 'r') as get_raw_params_file:
            get_raw_params = get_raw_params_file.read()

            result = payment.get_raw_params()

            h.hexdigest.assert_called_once_with()
            h.update.assert_any_call(payment.get_raw_params('&', False))
            h.update.assert_any_call(str(payment.commerce.id))
            h.update.assert_any_call("webpay")
            self.assertEqual(get_raw_params, result)

    def test_get_raw_params_sharp_no_pseudomac(self):
        """
        payment.get_raw_params returns params as seen on get_raw_params_sharp_no_pseudomac.txt
        """
        commerce = self.payment_kwargs['commerce']
        commerce.id = "1234567890"
        commerce.webpay_key_id = '101'
        payment = Payment(**self.payment_kwargs)
        payment._transaction_id = 123456789
        get_raw_params_file_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'raw_params_sharp_no_pseudomac.txt')
        with open(get_raw_params_file_path, 'r') as get_raw_params_file:
            get_raw_params = get_raw_params_file.read()
            result = payment.get_raw_params(include_pseudomac=False)
            self.assertEqual(get_raw_params, result)

    def test_get_raw_params_ampersand_no_pseudomac(self):
        """
        payment.get_raw_params returns params as seen on raw_params_ampersand_no_pseudomac.txt
        """
        commerce = self.payment_kwargs['commerce']
        commerce.id = "1234567890"
        commerce.webpay_key_id = '101'
        payment = Payment(**self.payment_kwargs)
        payment._transaction_id = 123456789
        get_raw_params_file_path = os.path.join(
            os.path.dirname(__file__), 'fixtures', 'raw_params_ampersand_no_pseudomac.txt')
        with open(get_raw_params_file_path, 'r') as get_raw_params_file:
            get_raw_params = get_raw_params_file.read()
            result = payment.get_raw_params(splitter="&", include_pseudomac=False)
            self.assertEqual(get_raw_params, result)

    def test_get_raw_params_ampersand_no_pseudomac_no_session_id(self):
        """
        payment.get_raw_params returns params as seen on get_raw_params_sharp_no_pseudomac_no_session.txt
        """
        commerce = self.payment_kwargs['commerce']
        commerce.id = "1234567890"
        commerce.webpay_key_id = '101'
        self.payment_kwargs['session_id'] = None
        payment = Payment(**self.payment_kwargs)
        payment._transaction_id = 123456789
        get_raw_params_file_path = os.path.join(
            os.path.dirname(__file__), 'fixtures', 'raw_params_sharp_no_pseudomac_no_session.txt')
        with open(get_raw_params_file_path, 'r') as get_raw_params_file:
            get_raw_params = get_raw_params_file.read()
            result = payment.get_raw_params(include_pseudomac=False)
            self.assertEqual(get_raw_params, result)

    @mock.patch('tbk.webpay.payment.random')
    def test_transaction_id(self, random):
        """
        payment.get_transaction_id returns a random int between 0 and 10000000000
        """
        random.randint.return_value = 123456789
        payment = Payment(**self.payment_kwargs)

        self.assertEqual(random.randint.return_value,
                         payment.transaction_id)
        random.randint.assert_called_once_with(0, 10000000000 - 1)

    def test_transaction_id_already_created(self):
        """
        payment.get_transaction_id returns a the same random int between 0 and 10000000000 the second time
        """
        payment = Payment(**self.payment_kwargs)
        first_result = payment.transaction_id

        self.assertEqual(first_result,
                         payment.transaction_id)

    def test_verify(self):
        payment = Payment(**self.payment_kwargs)

        self.assertEqual(None, payment.verify())

    def test_verify_no_commerce(self):
        payment = Payment(**self.payment_kwargs)
        payment.commerce = None

        six.assertRaisesRegex(self, 
            PaymentError, "Commerce required",
            payment.verify
        )

    def test_verify_amount_lt0(self):
        payment = Payment(**self.payment_kwargs)
        payment.amount = None

        six.assertRaisesRegex(self, 
            PaymentError, "Invalid amount None",
            payment.verify
        )
        payment.amount = Decimal("0")
        six.assertRaisesRegex(self, 
            PaymentError, "Invalid amount 0",
            payment.verify
        )

        payment.amount = Decimal("-1000")

        six.assertRaisesRegex(self, 
            PaymentError, "Invalid amount -100",
            payment.verify
        )

    def test_verify_no_order_id(self):
        payment = Payment(**self.payment_kwargs)
        payment.order_id = None

        six.assertRaisesRegex(self, 
            PaymentError, "Order ID required",
            payment.verify
        )

    def test_verify_no_success_url(self):
        payment = Payment(**self.payment_kwargs)
        payment.success_url = None

        six.assertRaisesRegex(self, 
            PaymentError, "Success URL required",
            payment.verify
        )

    def test_verify_no_confirmation_url(self):
        payment = Payment(**self.payment_kwargs)
        payment.confirmation_url = None

        six.assertRaisesRegex(self, 
            PaymentError, "Confirmation URL required",
            payment.verify
        )

    def test_verify_no_confirmation_ip(self):
        payment = Payment(**self.payment_kwargs)
        payment.confirmation_url = "http://example.org/confirmation"

        six.assertRaisesRegex(self, 
            PaymentError, "Confirmation URL host MUST be an IP address",
            payment.verify
        )

    def test_error_page(self):
        with open(os.path.join(os.path.dirname(__file__), 'fixtures', 'payment_error.txt')) as f:
            error_page = f.read()
        self.assertEqual(error_page, Payment.ERROR_PAGE)

    def test_get_form(self):
        payment = Payment(**self.payment_kwargs)
        commerce = self.payment_kwargs['commerce']
        commerce.id = '597026007976'
        commerce.webpay_key_id = '101'
        commerce.webpay_encrypt.return_value = 'param-mock'

        with open(os.path.join(os.path.dirname(__file__), 'fixtures', 'payment_form.txt')) as f:
            payment_form = f.read()

        self.assertEqual(payment_form, payment.get_form())


import sys
import re

import requests

from .commerce import Commerce
from .logging import logger
from .config import TBK_VERSION_KCC

__all__ = ['Payment', 'PaymentError']

REDIRECT_URL = "%(process_url)s?TBK_VERSION_KCC=%(tbk_version)s&TBK_TOKEN=%(token)s"
PYTHON_VERSION = "%d.%d" % (sys.version_info.major, sys.version_info.minor)
USER_AGENT = "TBK/%(TBK_VERSION_KCC)s (Python/%(PYTHON_VERSION)s)" % {
    'TBK_VERSION_KCC': TBK_VERSION_KCC,
    'PYTHON_VERSION': PYTHON_VERSION
}
ERROR_REGEXP = re.compile(r'.*(ERROR=)([a-zA-Z0-9]+).*')
TOKEN_REGEXP = re.compile(r'.*(TOKEN=)([a-zA-Z0-9]+).*')


class Payment(object):
    _token = None
    _params = None

    def __init__(self, request_ip, amount,
                 order_id, success_url, confirmation_url,
                 session_id=None, failure_url=None, commerce=None,
                 config=None):
        self.commerce = commerce or Commerce.create_commerce(config)
        self.request_ip = request_ip
        self.amount = amount
        self.order_id = order_id
        self.success_url = success_url
        self.confirmation_url = confirmation_url
        self.session_id = session_id
        self.failure_url = failure_url or success_url

    @property
    def redirect_url(self):
        return REDIRECT_URL % {
            'tbk_version': TBK_VERSION_KCC,
            'process_url': self.process_url(),
            'token': self.token()
        }

    def token(self):
        if not self._token:
            self._token = self.fetch_token()
            logger.payment(self)
        return self._token

    def fetch_token(self):
        response = requests.post(
            self.process_url(),
            data={
                'TBK_VERSION_KCC': TBK_VERSION_KCC,
                'TBK_CODIGO_COMERCIO': self.commerce.id,
                'TBK_KEY_ID': self.commerce.webpay_key_id,
                'TBK_PARAM': self.params()
            },
            headers={
                'User-Agent': USER_AGENT
            }
        )
        if response.status_code != 200:
            raise PaymentError("Payment token generation failed")

        body = self.commerce.webpay_decrypt(response.content)['body']

        return self.get_token_from_body(body)

    def get_token_from_body(self, body):
        error_match = ERROR_REGEXP.match(body)
        if error_match.group(2) != "0":
            raise PaymentError("Payment token generation failed. ERROR=%s" % error_match.group(2))
        token_match = TOKEN_REGEXP.match(body)
        return token_match.group(2)

    def process_url(self):
        if self.commerce.testing:
            return "https://certificacion.webpay.cl:6443/filtroUnificado/bp_revision.cgi"
        return "https://webpay.transbank.cl:443/filtroUnificado/bp_revision.cgi"

    def validation_url(self):
        if self.commerce.testing:
            return "https://certificacion.webpay.cl:6443/filtroUnificado/bp_validacion.cgi"
        return "https://webpay.transbank.cl:443/filtroUnificado/bp_validacion.cgi"

    def params(self):
        if not self._params:
            self.verify()
            self._params = self.commerce.webpay_encrypt(self.raw_params())
        return self._params

    def verify(self):
        pass

    def raw_params(self):
        pass


class PaymentError(Exception):
    pass

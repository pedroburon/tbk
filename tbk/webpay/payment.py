import sys
import random
import hashlib
import re
import decimal

from six.moves.urllib.parse import urlparse

import requests

from .commerce import Commerce
from .logging import logger
from . import TBK_VERSION_KCC

__all__ = ['Payment', 'PaymentError']

REDIRECT_URL = "%(process_url)s?TBK_VERSION_KCC=%(tbk_version)s&TBK_TOKEN=%(token)s"
PYTHON_VERSION = "%d.%d" % (sys.version_info.major, sys.version_info.minor)
USER_AGENT = "TBK/%(TBK_VERSION_KCC)s (Python/%(PYTHON_VERSION)s)" % {
    'TBK_VERSION_KCC': TBK_VERSION_KCC,
    'PYTHON_VERSION': PYTHON_VERSION
}


class Payment(object):
    _token = None
    _params = None
    _transaction_id = None

    def __init__(self, request_ip, amount,
                 order_id, success_url, confirmation_url,
                 session_id=None, failure_url=None, commerce=None,):
        self.commerce = commerce or Commerce.create_commerce()
        self.request_ip = request_ip
        self.amount = self.__get_amount(amount)
        self.order_id = order_id
        self.success_url = success_url
        self.confirmation_url = confirmation_url
        self.session_id = session_id
        self.failure_url = failure_url or success_url

    def __get_amount(self, amount):
        return decimal.Decimal(str(amount)).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)

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
        validation_url = self.validation_url()
        is_redirect = True

        while is_redirect:
            response = requests.post(
                validation_url,
                data={
                    'TBK_VERSION_KCC': TBK_VERSION_KCC,
                    'TBK_CODIGO_COMERCIO': self.commerce.id,
                    'TBK_KEY_ID': self.commerce.webpay_key_id,
                    'TBK_PARAM': self.params()
                },
                headers={
                    'User-Agent': USER_AGENT
                },
                allow_redirects=False
            )
            is_redirect = response.is_redirect
            validation_url = response.headers.get('location')

        if response.status_code != 200:
            raise PaymentError("Payment token generation failed")

        body, _ = self.commerce.webpay_decrypt(response.content)

        return self.get_token_from_body(body)

    def get_token_from_body(self, body):
        TOKEN = 'TOKEN='
        ERROR = 'ERROR='
        lines = body.strip().split('\n')
        for line in lines:
            if line.startswith(TOKEN):
                token = line[len(TOKEN):]
            elif line.startswith(ERROR):
                error = line[len(ERROR):]
        if error != '0':
            raise PaymentError("Payment token generation failed. ERROR=%s" % error)
        return token

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
        if self.commerce is None:
            raise PaymentError("Commerce required")
        if self.amount is None or self.amount <= 0:
            raise PaymentError("Invalid amount %s" % self.amount)
        if self.order_id is None:
            raise PaymentError("Order ID required")
        if self.success_url is None:
            raise PaymentError("Success URL required")
        if self.confirmation_url is None:
            raise PaymentError("Confirmation URL required")
        confirmation_uri = urlparse(self.confirmation_url)
        if re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', confirmation_uri.hostname) is None:
            raise PaymentError("Confirmation URL host MUST be an IP address")

    def transaction_id(self):
        if not self._transaction_id:
            self._transaction_id = random.randint(0, 10000000000 - 1)
        return self._transaction_id

    def raw_params(self, splitter="#", include_pseudomac=True):
        params = []
        params += ["TBK_ORDEN_COMPRA=%s" % self.order_id]
        params += ["TBK_CODIGO_COMERCIO=%s" % self.commerce.id]
        params += ["TBK_ID_TRANSACCION=%s" % self.transaction_id()]
        uri = urlparse(self.confirmation_url)
        params += ["TBK_URL_CGI_COMERCIO=%s" % uri.path]
        params += ["TBK_SERVIDOR_COMERCIO=%s" % uri.hostname]
        params += ["TBK_PUERTO_COMERCIO=%s" % uri.port]
        params += ["TBK_VERSION_KCC=%s" % TBK_VERSION_KCC]
        params += ["TBK_KEY_ID=%s" % self.commerce.webpay_key_id]
        params += ["PARAMVERIFCOM=1"]

        if include_pseudomac:
            h = hashlib.new('md5')
            h.update(self.raw_params('&', False))
            h.update(str(self.commerce.id))
            h.update("webpay")
            mac = str(h.hexdigest())

            params += ["TBK_MAC=%s" % mac]

        params += ["TBK_MONTO=%d" % int(self.amount * 100)]
        if self.session_id:
            params += ["TBK_ID_SESION=%s" % self.session_id]
        params += ["TBK_URL_EXITO=%s" % self.success_url]
        params += ["TBK_URL_FRACASO=%s" % self.failure_url]
        params += ["TBK_TIPO_TRANSACCION=TR_NORMAL"]
        return splitter.join(params)


class PaymentError(Exception):
    pass

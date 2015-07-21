import sys
import hashlib
import re
import decimal

import six
import requests
from Crypto.Random import random

from .commerce import Commerce, DecryptionError
from .params import Params
from .logging import logger
from . import TBK_VERSION_KCC

__all__ = ['Payment', 'PaymentError']

REDIRECT_URL = "%(process_url)s?TBK_VERSION_KCC=%(tbk_version)s&TBK_TOKEN=%(token)s"
PYTHON_VERSION = "%d.%d" % (sys.version_info.major, sys.version_info.minor)
USER_AGENT = "TBK/%(TBK_VERSION_KCC)s (Python/%(PYTHON_VERSION)s)" % {
    'TBK_VERSION_KCC': TBK_VERSION_KCC,
    'PYTHON_VERSION': PYTHON_VERSION
}

TBK_NORMAL_TRANSACTION = 'TR_NORMAL'


PAYMENT_FORM = ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">'
                '<html><head><title>WebPay</title><meta name="GENERATOR" content="www.orangepeople.cl" />'
                '<meta name="AUTHOR" content="Orange People Software LTDA" />'
                '<link rel="stylesheet" type="text/css" href="https://webpay.transbank.cl/images/documento.css" />'
                '<script language="javascript" charset="iso-8859-1" type="text/javascript" '
                'src="https://webpay.transbank.cl/images/documento.js"></script></head>'
                '<body onload="if (document.f != null) document.f.submit();">'
                '<div id="container"><div id="content"><div id="espaciar">'
                '<img src="https://webpay.transbank.cl/images/webpay.gif" alt="WebPay" /></div>'
                '<div id="barra" style="visibility:visible;">'
                '<img id="espera" src="https://webpay.transbank.cl/images/barra.gif" alt="Espere por favor" /></div>'
                '<div id="espaciar"><div id="err_div" style="visibility:hidden;">'
                '<h1>ERROR: No se ha podido establecer la conexi&oacute;n</h1>'
                '<a href="javascript:history.go(-2)">Volver al comercio</a></div></div></div></div>'
                '<form name="f" method="POST" action="{process_url}">\n'
                '<input type="hidden" name="TBK_PARAM" value="{TBK_PARAM}">\n'
                '<input type="hidden" name="TBK_VERSION_KCC" value="{TBK_VERSION_KCC}">\n'
                '<input type="hidden" name="TBK_CODIGO_COMERCIO" value="{TBK_CODIGO_COMERCIO}">\n'
                '<input type="hidden" name="TBK_KEY_ID" value="{TBK_KEY_ID}">\n'
                '</form>\n</body>\n</html>\n')


def get_token_from_body(body):
    TOKEN = 'TOKEN='
    ERROR = 'ERROR='
    if isinstance(body, six.binary_type):
        body = body.decode('utf-8')
    lines = body.strip().split('\n')
    for line in lines:
        if line.startswith(TOKEN):
            token = line[len(TOKEN):]
        elif line.startswith(ERROR):
            error = line[len(ERROR):]
    if error != '0':
        raise PaymentError("Payment token generation failed. ERROR=%s" % error)
    return token


def clean_amount(amount):
    return decimal.Decimal(str(amount)).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_UP)


class PaymentParams(Params):
    fields = (
        "TBK_ORDEN_COMPRA",
        "TBK_CODIGO_COMERCIO",
        "TBK_ID_TRANSACCION",
        "TBK_URL_CGI_COMERCIO",
        "TBK_SERVIDOR_COMERCIO",
        "TBK_PUERTO_COMERCIO",
        "TBK_VERSION_KCC",
        "TBK_KEY_ID",
        "PARAMVERIFCOM",
        "TBK_MAC",
        "TBK_MONTO",
        "TBK_ID_SESION",
        "TBK_URL_EXITO",
        "TBK_URL_FRACASO",
        "TBK_TIPO_TRANSACCION",
        "TBK_MONTO_CUOTA",
        "TBK_NUMERO_CUOTAS"
    )
    optionals = (
        "TBK_ID_SESION",
        "TBK_MONTO_CUOTA",
        "TBK_NUMERO_CUOTAS"
    )


class Payment(object):
    """
    Initialize a Payment object with params required to create the redirection url.
    """
    _token = None
    _params = None
    _transaction_id = None

    ERROR_PAGE = ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"><html>'
                  '<head><title>WebPay</title><meta name="GENERATOR" content="www.orangepeople.cl" />'
                  '<meta name="AUTHOR" content="Orange People Software LTDA" />'
                  '<link rel="stylesheet" type="text/css" href="https://webpay.transbank.cl/images/documento.css" />'
                  '<script language="javascript" charset="iso-8859-1" type="text/javascript" '
                  'src="https://webpay.transbank.cl/images/documento.js"></script>'
                  '</head><body onload="if (document.f != null) document.f.submit();">'
                  '<div id="container"><div id="content"><div id="espaciar">'
                  '<img src="https://webpay.transbank.cl/images/webpay.gif" alt="WebPay" /></div>'
                  '<div id="barra" style="visibility:visible;">'
                  '<img id="espera" src="https://webpay.transbank.cl/images/barra.gif" alt="Espere por favor" /></div>'
                  '<div id="espaciar"><div id="err_div" style="visibility:hidden;">'
                  '<h1>ERROR: No se ha podido establecer la conexi&oacute;n</h1>'
                  '<a href="javascript:history.go(-2)">Volver al comercio</a>'
                  '</div></div></div></div><script language=\'JavaScript\'>'
                  'ShowContent(\'err_div\');NoShowContent(\'barra\');</script><br /><!-- Codigo Error: 1 --><br />')

    def __init__(self, request_ip, amount,
                 order_id, success_url, confirmation_url,
                 session_id=None, failure_url=None, commerce=None,
                 installments=0, installments_amount=None):
        self.commerce = commerce or Commerce.create_commerce()
        self.request_ip = request_ip
        self.amount = clean_amount(amount)
        self.order_id = order_id
        self.success_url = success_url
        self.confirmation_url = confirmation_url
        self.session_id = session_id
        self.failure_url = failure_url or success_url

    @property
    def redirect_url(self):
        """
        Redirect user to this URL and will begin the payment process.

        Will raise PaymentError when an error ocurred.
        """
        return REDIRECT_URL % {
            'tbk_version': TBK_VERSION_KCC,
            'process_url': self.get_process_url(),
            'token': self.token
        }

    @property
    def token(self):
        """
        Token given by Transbank for payment initialization url.

        Will raise PaymentError when an error ocurred.
        """
        if not self._token:
            self._token = self.fetch_token()
            logger.payment(self)
        return self._token

    def fetch_token(self):
        validation_url = self.get_validation_url()
        is_redirect = True

        while is_redirect:
            response = requests.post(
                validation_url,
                data={
                    'TBK_VERSION_KCC': TBK_VERSION_KCC,
                    'TBK_CODIGO_COMERCIO': self.commerce.id,
                    'TBK_KEY_ID': self.commerce.webpay_key_id,
                    'TBK_PARAM': self.params
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

        try:
            body, _ = self.commerce.webpay_decrypt(response.content)
        except DecryptionError:
            if get_token_from_body(response.content):
                raise PaymentError("Suspicious message from server: %s" % response.content)

        return get_token_from_body(body)

    def get_process_url(self):
        if self.commerce.testing:
            return "https://certificacion.webpay.cl:6443/filtroUnificado/bp_revision.cgi"
        return "https://webpay.transbank.cl:443/filtroUnificado/bp_revision.cgi"

    def get_validation_url(self):
        if self.commerce.testing:
            return "https://certificacion.webpay.cl:6443/filtroUnificado/bp_validacion.cgi"
        return "https://webpay.transbank.cl:443/filtroUnificado/bp_validacion.cgi"

    @property
    def params(self):
        if not self._params:
            self.verify()
            self._params = self.commerce.webpay_encrypt(self.get_raw_params())
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
        confirmation_uri = six.moves.urllib.parse.urlparse(self.confirmation_url)
        if re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', confirmation_uri.hostname) is None:
            raise PaymentError("Confirmation URL host MUST be an IP address")
        if confirmation_uri.scheme not in ('http', 'https') and not confirmation_uri.port:
            raise PaymentError("Confirmation URL scheme MUST be http or https if port not specified.")

    @property
    def transaction_id(self):
        """
        Transaction ID for Transbank, a secure random int between 0 and 999999999.
        """
        if not self._transaction_id:
            self._transaction_id = random.randint(0, 10000000000 - 1)
        return self._transaction_id

    def get_raw_params(self):
        params = PaymentParams(commerce=self.commerce)
        params['TBK_ORDEN_COMPRA'] = self.order_id
        params['TBK_CODIGO_COMERCIO'] = self.commerce.id
        params['TBK_ID_TRANSACCION'] = self.transaction_id
        uri = six.moves.urllib.parse.urlparse(self.confirmation_url)
        params['TBK_URL_CGI_COMERCIO'] = uri.path
        params['TBK_SERVIDOR_COMERCIO'] = uri.hostname
        params['TBK_PUERTO_COMERCIO'] = uri.port or (443 if uri.scheme == 'https' else 80)
        params['TBK_VERSION_KCC'] = TBK_VERSION_KCC
        params['TBK_KEY_ID'] = self.commerce.webpay_key_id
        params['PARAMVERIFCOM'] = 1
        params["TBK_MONTO"] = int(self.amount * 100)
        if self.session_id:
            params["TBK_ID_SESION"] = self.session_id
        params["TBK_URL_EXITO"] = self.success_url
        params["TBK_URL_FRACASO"] = self.failure_url
        params["TBK_TIPO_TRANSACCION"] = TBK_NORMAL_TRANSACTION
        return params.get_raw()

    def get_form(self):
        return PAYMENT_FORM.format(
            process_url=self.get_process_url(),
            TBK_PARAM=self.params,
            TBK_VERSION_KCC=TBK_VERSION_KCC,
            TBK_CODIGO_COMERCIO=self.commerce.id,
            TBK_KEY_ID=self.commerce.webpay_key_id
        )


class PaymentError(Exception):
    pass

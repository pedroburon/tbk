# encoding=UTF-8
from __future__ import unicode_literals

import decimal
import datetime
import warnings

import pytz

from .logging import logger

from . import CONFIRMATION_TIMEOUT


class ConfirmationPayload(object):
    ''' A convenient class to handle Webpay Transaction Payload.
    '''
    RESPONSE_CODES = {
        0: 'Transacción aprobada.',
        -1: 'Rechazo de tx. en B24, No autorizada',
        -2: 'Transacción debe reintentarse.',
        -3: 'Error en tx.',
        -4: 'Rechazo de tx. En B24, No autorizada',
        -5: 'Rechazo por error de tasa.',
        -6: 'Excede cupo máximo mensual.',
        -7: 'Excede límite diario por transacción.',
        -8: 'Rubro no autorizado.'
    }
    SUCCESS_RESPONSE_CODE = 0
    PAYMENT_TYPES = {
        "VN": "Venta Normal",
        "VC": "Venta Cuotas",
        "SI": "Tres Cuotas Sin Interés",
        "S2": "Dos Cuotas Sin Interés",
        "CI": "Cuotas Comercio",
        "VD": "Redcompra",
    }

    def __init__(self, data):
        self.data = data

    @property
    def paid_at(self):
        '''Localized at America/Santiago datetime of ``TBK_FECHA_TRANSACCION``.
        '''
        fecha_transaccion = self.data['TBK_FECHA_TRANSACCION']
        hora_transaccion = self.data['TBK_HORA_TRANSACCION']
        m = int(fecha_transaccion[:2])
        d = int(fecha_transaccion[2:])
        h = int(hora_transaccion[:2])
        i = int(hora_transaccion[2:4])
        s = int(hora_transaccion[4:])

        santiago = pytz.timezone('America/Santiago')
        today = santiago.localize(datetime.datetime.today())
        santiago_dt = santiago.localize(
            datetime.datetime(today.year, m, d, h, i, s))

        return santiago_dt

    @property
    def message(self):
        '''Message corresponding to response code ``TBK_RESPUESTA``.
        '''
        return self.RESPONSE_CODES[self.response]

    @property
    def amount(self):
        '''Amount sent in ``TBK_MONTO`` as a Decimal.
        '''
        return decimal.Decimal(self.data['TBK_MONTO']) / 100

    @property
    def transaction_id(self):
        '''Transaction ID as int.
        '''
        return int(self.data['TBK_ID_TRANSACCION'])

    @property
    def order_id(self):
        '''Order ID from ``TBK_ORDEN_COMPRA`` as string.
        '''
        return self.data['TBK_ORDEN_COMPRA']

    @property
    def response(self):
        '''Response code as int (``TBK_RESPUESTA``)
        '''
        return int(self.data['TBK_RESPUESTA'])

    @property
    def credit_card_last_digits(self):
        '''Last 4 digits of the card used by customer.
        '''
        return self.data['TBK_FINAL_NUMERO_TARJETA']

    @property
    def credit_card_number(self):
        ''' 12 digits credit card string, only showing last digits.
        '''
        return "XXXX-XXXX-XXXX-{last_digits}".format(last_digits=self.credit_card_last_digits)

    @property
    def authorization_code(self):
        '''Transaction authorization code.
        '''
        return self.data['TBK_CODIGO_AUTORIZACION']

    @property
    def accountable_date(self):
        '''Accountable date of transaction, localized as America/Santiago
        '''
        fecha_transaccion = self.data['TBK_FECHA_CONTABLE']
        m = int(fecha_transaccion[:2])
        d = int(fecha_transaccion[2:])
        santiago = pytz.timezone('America/Santiago')
        today = santiago.localize(datetime.datetime.today())
        year = today.year
        if self.paid_at.month == 12 and m == 1:
            year += 1
        santiago_dt = santiago.localize(datetime.datetime(year, m, d))
        return santiago_dt

    @property
    def session_id(self):
        '''Session id, if 'null' then ``None``
        '''
        session_id = self.data['TBK_ID_SESION']
        return session_id if session_id != 'null' else None

    @property
    def installments(self):
        '''Quantity of installments
        '''
        return int(self.data['TBK_NUMERO_CUOTAS'])

    @property
    def payment_type(self):
        '''Payment Type according to ``TBK_TIPO_PAGO``.
        '''
        return self.PAYMENT_TYPES[self.payment_type_code]

    @property
    def payment_type_code(self):
        '''Payment type code according to ``TBK_TIPO_PAGO``.
        '''
        return self.data['TBK_TIPO_PAGO']

    def __getitem__(self, key):
        return self.data[key]


class Confirmation(object):
    '''
    Create a confirmation instance which handle callback data from transbank.

    Given that Webpay accept acknowledge response only in less than 30 seconds,
    there is a timeout of 25 seconds (by default) for suceed the answer.

    :param commerce: Commerce instance corresponding to ``data['TBK_ID_COMERCIO']``.
    :param request_ip: String representing request ip.
    :param data: dict like instance with ``TBK_PARAM``.
    :param timeout: seconds between initialization and ``is_success`` to don't suceed.
    '''

    def __init__(self, commerce, request_ip, data, timeout=CONFIRMATION_TIMEOUT):
        self.init_time = datetime.datetime.now()
        self.timeout = timeout
        self.commerce = commerce
        self.request_ip = request_ip
        self.payload = ConfirmationPayload(self.parse(data['TBK_PARAM']))

    def parse(self, tbk_param):
        decrypted_params, signature = self.commerce.webpay_decrypt(tbk_param)
        params = {}
        for line in decrypted_params.split('#'):
            index = line.find('=')
            params[line[:index]] = line[index + 1:]
        params['TBK_MAC'] = signature
        return params

    def validate_order(self, validate_func, check_timeout=True):
        if self.is_success(check_timeout) and validate_func(self.payload):
            logger.confirmation(self)
            return True
        if self.is_valid(check_timeout):
            logger.confirmation(self)
            return False
        logger.error(self)
        return False
    
    def is_valid(self, check_timeout=True):
        '''
        Check if Webpay response ``TBK_RESPUESTA`` is distinct to ``0`` and if the lapse between initialization
        and this call is less than ``self.timeout`` when ``check_timeout`` is ``True`` (default).

        :param check_timeout: When ``True``, check time between initialization and call.
        '''
        if check_timeout and self.is_timeout():
            return False
        return self.payload.response  != 0
    
    def is_success(self, check_timeout=True):
        '''
        Check if Webpay response ``TBK_RESPUESTA`` is equal to ``0`` and if the lapse between initialization
        and this call is less than ``self.timeout`` when ``check_timeout`` is ``True`` (default).

        :param check_timeout: When ``True``, check time between initialization and call.
        '''
        if check_timeout and self.is_timeout():
            return False
        return self.payload.response == self.payload.SUCCESS_RESPONSE_CODE

    def is_timeout(self):
        '''
        Check if the lapse between initialization and now is more than ``self.timeout``.
        '''
        lapse = datetime.datetime.now() - self.init_time
        return lapse > datetime.timedelta(seconds=self.timeout)

    @property
    def amount(self):
        '''
        Amount sent by Webpay.

        :rtype: ``decimal.Decimal``
        '''
        return self.payload.amount

    @property
    def order_id(self):
        '''
        Order id sent by Webpay.
        '''
        return self.payload.order_id

    # DEPRECATED

    @property
    def acknowledge(self):  # pragma: no cover
        warnings.warn(
            "Deprecated for commerce.acknowledge. Will not be longer available at v1.0.0.", DeprecationWarning)
        return self.commerce.acknowledge

    @property
    def reject(self):  # pragma: no cover
        warnings.warn(
            "Deprecated for commerce.reject. Will not be longer available at v1.0.0.", DeprecationWarning)
        return self.commerce.reject

    @property
    def message(self):  # pragma: no cover
        warnings.warn(
            "Deprecated for payload.message. Will not be longer available at v1.0.0.", DeprecationWarning)
        return self.payload.message

    @property
    def paid_at(self):  # pragma: no cover
        warnings.warn(
            "Deprecated for payload.paid_at. Will not be longer available at v1.0.0.", DeprecationWarning)
        return self.payload.paid_at

    @property
    def transaction_id(self):  # pragma: no cover
        warnings.warn(
            "Deprecated for payload.transaction_id. Will not be longer available at v1.0.0.", DeprecationWarning)
        return self.payload.transaction_id

    @property
    def params(self):  # pragma: no cover
        warnings.warn(
            "Deprecated for payload.data. Will not be longer available at v1.0.0.", DeprecationWarning)
        return self.payload.data

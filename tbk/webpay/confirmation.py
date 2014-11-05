# encoding=UTF-8
from __future__ import unicode_literals

import decimal
import datetime
import warnings

import pytz

from .logging import logger


class ConfirmationPayload(object):
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
        "CI": "Cuotas Comercio"
    }

    def __init__(self, data):
        self.data = data

    @property
    def paid_at(self):
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
        return self.RESPONSE_CODES[self.response]

    @property
    def amount(self):
        return decimal.Decimal(self.data['TBK_MONTO']) / 100

    @property
    def transaction_id(self):
        return int(self.data['TBK_ID_TRANSACCION'])

    @property
    def order_id(self):
        return self.data['TBK_ORDEN_COMPRA']

    @property
    def response(self):
        return int(self.data['TBK_RESPUESTA'])

    @property
    def credit_card_last_digits(self):
        return self.data['TBK_FINAL_NUMERO_TARJETA']

    @property
    def credit_card_number(self):
        return "XXXX-XXXX-XXXX-{last_digits}".format(last_digits=self.credit_card_last_digits)

    @property
    def authorization_code(self):
        return self.data['TBK_CODIGO_AUTORIZACION']

    @property
    def accountable_date(self):
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
        session_id = self.data['TBK_ID_SESION']
        return session_id if session_id != 'null' else None

    @property
    def installments(self):
        return int(self.data['TBK_NUMERO_CUOTAS'])

    @property
    def payment_type(self):
        return self.PAYMENT_TYPES[self.payment_type_code]

    @property
    def payment_type_code(self):
        return self.data['TBK_TIPO_PAGO']

    def __getitem__(self, key):
        return self.data[key]


class Confirmation(object):

    def __init__(self, commerce, request_ip, data):
        self.commerce = commerce
        self.request_ip = request_ip
        self.payload = ConfirmationPayload(self.parse(data['TBK_PARAM']))
        logger.confirmation(self)

    def parse(self, tbk_param):
        decrypted_params, signature = self.commerce.webpay_decrypt(tbk_param)
        params = {}
        for line in decrypted_params.split('#'):
            index = line.find('=')
            params[line[:index]] = line[index + 1:]
        params['TBK_MAC'] = signature
        return params

    def is_success(self):
        return self.payload.response == self.payload.SUCCESS_RESPONSE_CODE

    @property
    def amount(self):
        return self.payload.amount

    @property
    def order_id(self):
        return self.payload.order_id

    @property
    def acknowledge(self):  # pragma: no cover
        warnings.warn(
            "Deprecated for commerce.acknowledge attribute.", DeprecationWarning)
        return self.commerce.acknowledge

    @property
    def reject(self):  # pragma: no cover
        warnings.warn(
            "Deprecated for commerce.reject attribute.", DeprecationWarning)
        return self.commerce.reject

    @property
    def message(self):  # pragma: no cover
        warnings.warn(
            "Deprecated for payload.message attribute.", DeprecationWarning)
        return self.payload.message

    @property
    def paid_at(self):  # pragma: no cover
        warnings.warn(
            "Deprecated for payload.paid_at attribute.", DeprecationWarning)
        return self.payload.paid_at

    @property
    def transaction_id(self):  # pragma: no cover
        warnings.warn(
            "Deprecated for payload.transaction_id attribute.", DeprecationWarning)
        return self.payload.transaction_id

    @property
    def params(self):  # pragma: no cover
        warnings.warn(
            "Deprecated for payload.data attribute.", DeprecationWarning)
        return self.payload.data

# encoding=UTF-8
from __future__ import unicode_literals

import decimal
import datetime

import pytz

from .logging import logger


class Confirmation(object):
    RESPONSE_CODES = {
        '0': 'Transacción aprobada.',
        '-1': 'Rechazo de tx. en B24, No autorizada',
        '-2': 'Transacción debe reintentarse.',
        '-3': 'Error en tx.',
        '-4': 'Rechazo de tx. En B24, No autorizada',
        '-5': 'Rechazo por error de tasa.',
        '-6': 'Excede cupo máximo mensual.',
        '-7': 'Excede límite diario por transacción.',
        '-8': 'Rubro no autorizado.'
    }

    def __init__(self, commerce, request_ip, data):
        self.commerce = commerce
        self.request_ip = request_ip
        self.params = self.parse(data['TBK_PARAM'])
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
        return self.params['TBK_RESPUESTA'] == '0'

    @property
    def acknowledge(self):
        return self.commerce.webpay_encrypt('ACK')

    @property
    def reject(self):
        return self.commerce.webpay_encrypt('ERR')

    @property
    def message(self):
        return self.RESPONSE_CODES[self.params['TBK_RESPUESTA']]

    @property
    def paid_at(self):
        fecha_transaccion = self.params['TBK_FECHA_TRANSACCION']
        hora_transaccion = self.params['TBK_HORA_TRANSACCION']
        m = int(fecha_transaccion[:2])
        d = int(fecha_transaccion[2:])
        h = int(hora_transaccion[:2])
        i = int(hora_transaccion[2:4])
        s = int(hora_transaccion[4:])

        santiago = pytz.timezone('America/Santiago')
        today = santiago.localize(datetime.datetime.today())
        santiago_dt = santiago.localize(datetime.datetime(today.year, m, d, h, i, s))

        return santiago_dt

    @property
    def amount(self):
        return decimal.Decimal(self.params['TBK_MONTO']) / 100

    @property
    def transaction_id(self):
        return int(self.params['TBK_ID_TRANSACCION'])

    @property
    def order_id(self):
        return self.params['TBK_ORDEN_COMPRA']

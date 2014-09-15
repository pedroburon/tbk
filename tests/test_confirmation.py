# encoding=UTF-8
from __future__ import unicode_literals

import os
from unittest import TestCase
import datetime

import mock
import pytz

from tbk.webpay.confirmation import Confirmation


CONFIRMATION_DATA = {
    'TBK_CODIGO_AUTORIZACION': '001882',
    'TBK_FECHA_CONTABLE': '0123',
    'TBK_FECHA_TRANSACCION': '0123',
    'TBK_FINAL_NUMERO_TARJETA': '9509',
    'TBK_HORA_TRANSACCION': '150959',
    'TBK_ID_SESION': '430c2c85',
    'TBK_ID_TRANSACCION': '2164532727',
    'TBK_MONTO': '10000',
    'TBK_NUMERO_CUOTAS': '0',
    'TBK_ORDEN_COMPRA': '3244',
    'TBK_RESPUESTA': '0',
    'TBK_TIPO_PAGO': 'VD',
    'TBK_TIPO_TRANSACCION': 'TR_NORMAL',
    'TBK_VCI': 'TSY'
}


class ConfirmationTest(TestCase):

    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_init(self, parse):
        commerce = mock.Mock()
        request_ip = "123.123.123.123"
        data = {
            'TBK_PARAM': mock.Mock()
        }

        confirmation = Confirmation(commerce, request_ip, data)

        self.assertEqual(commerce, confirmation.commerce)
        self.assertEqual(request_ip, confirmation.request_ip)
        self.assertEqual(parse.return_value, confirmation.params)
        parse.assert_called_once_with(data['TBK_PARAM'])

    def test_init_wo_tbk_param(self):
        commerce = mock.Mock()
        request_ip = "123.123.123.123"
        data = {}

        self.assertRaises(KeyError, Confirmation, commerce, request_ip, data)

    # @mock.patch('tbk.webpay.confirmation.logger')
    def test_parse(self):
        with open(os.path.join(os.path.dirname(__file__), 'fixtures', 'confirmation.txt')) as f:
            confirmation_data = f.read()
        data = {
            'TBK_PARAM': mock.Mock()
        }
        commerce = mock.Mock()
        commerce.webpay_decrypt.return_value = (confirmation_data, "signature")
        request_ip = "123.123.123.123"

        confirmation = Confirmation(commerce, request_ip, data)

        params = CONFIRMATION_DATA.copy()
        params['TBK_MAC'] = "signature"

        self.assertEqual(params, confirmation.params)
        commerce.webpay_decrypt.assert_called_once_with(data['TBK_PARAM'])
        # logger.confirmation.assert_called_once_with(confirmation)

    @mock.patch('tbk.webpay.confirmation.logger')
    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_is_success(self, parse, logger):
        parse.return_value = {
            'TBK_RESPUESTA': '0',
        }
        commerce = mock.Mock()
        request_ip = "123.123.123.123"
        data = {
            'TBK_PARAM': mock.Mock()
        }

        confirmation = Confirmation(commerce, request_ip, data)

        self.assertTrue(confirmation.is_success())

    @mock.patch('tbk.webpay.confirmation.logger')
    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_is_success_respuesta_not_0(self, parse, logger):
        commerce = mock.Mock()
        request_ip = "123.123.123.123"
        data = {
            'TBK_PARAM': mock.Mock()
        }

        for i in range(1, 10):
            parse.return_value = {
                'TBK_RESPUESTA': str(-i),
            }
            confirmation = Confirmation(commerce, request_ip, data)
            self.assertFalse(confirmation.is_success())

    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_acknowledge(self, parse):
        commerce = mock.Mock()
        request_ip = "123.123.123.123"
        data = {
            'TBK_PARAM': mock.Mock()
        }
        confirmation = Confirmation(commerce, request_ip, data)

        self.assertEqual(confirmation.acknowledge, commerce.webpay_encrypt.return_value)
        commerce.webpay_encrypt.assert_called_once_with("ACK")

    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_reject(self, parse):
        commerce = mock.Mock()
        request_ip = "123.123.123.123"
        data = {
            'TBK_PARAM': mock.Mock()
        }
        confirmation = Confirmation(commerce, request_ip, data)

        self.assertEqual(confirmation.reject, commerce.webpay_encrypt.return_value)
        commerce.webpay_encrypt.assert_called_once_with("ERR")

    @mock.patch('tbk.webpay.confirmation.logger')
    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_messages(self, parse, logger):
        commerce = mock.Mock()
        request_ip = "123.123.123.123"
        data = {
            'TBK_PARAM': mock.Mock()
        }
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

        for i in RESPONSE_CODES.keys():
            parse.return_value = {
                'TBK_RESPUESTA': str(i),
            }
            confirmation = Confirmation(commerce, request_ip, data)
            self.assertEqual(RESPONSE_CODES[i], confirmation.message)

    @mock.patch('tbk.webpay.confirmation.logger')
    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_paid_at(self, parse, logger):
        santiago = pytz.timezone('America/Santiago')
        today = santiago.localize(datetime.datetime.today())
        santiago_dt = santiago.localize(datetime.datetime(today.year, 1, 23, 15, 9, 59))

        commerce = mock.Mock()
        request_ip = "123.123.123.123"
        data = {
            'TBK_PARAM': mock.Mock()
        }
        parse.return_value = {
            'TBK_FECHA_TRANSACCION': '0123',
            'TBK_HORA_TRANSACCION': '150959',
        }
        confirmation = Confirmation(commerce, request_ip, data)
        self.assertEqual(santiago_dt, confirmation.paid_at)

    @mock.patch('tbk.webpay.confirmation.logger')
    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_amount(self, parse, logger):
        commerce = mock.Mock()
        request_ip = "123.123.123.123"
        data = {
            'TBK_PARAM': mock.Mock()
        }
        parse.return_value = {
            'TBK_MONTO': '1234500',
        }
        confirmation = Confirmation(commerce, request_ip, data)

        self.assertEqual(12345, confirmation.amount)

    @mock.patch('tbk.webpay.confirmation.logger')
    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_transaction_id(self, parse, logger):
        commerce = mock.Mock()
        request_ip = "123.123.123.123"
        data = {
            'TBK_PARAM': mock.Mock()
        }
        parse.return_value = {
            'TBK_ID_TRANSACCION': '1234500',
        }
        confirmation = Confirmation(commerce, request_ip, data)

        self.assertEqual(1234500, confirmation.transaction_id)

    @mock.patch('tbk.webpay.confirmation.logger')
    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_order_id(self, parse, logger):
        commerce = mock.Mock()
        request_ip = "123.123.123.123"
        data = {
            'TBK_PARAM': mock.Mock()
        }
        parse.return_value = {
            'TBK_ORDEN_COMPRA': '123asd4500',
        }
        confirmation = Confirmation(commerce, request_ip, data)

        self.assertEqual('123asd4500', confirmation.order_id)

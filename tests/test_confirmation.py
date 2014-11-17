# encoding=UTF-8
from __future__ import unicode_literals

import os
from unittest import TestCase
import datetime
from decimal import Decimal

import mock
import pytz

from tbk.webpay.confirmation import Confirmation, ConfirmationPayload


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

    def setUp(self):
        self.request_ip = "123.123.123.123"
        self.commerce = mock.Mock()

    @mock.patch('tbk.webpay.confirmation.ConfirmationPayload')
    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_init(self, parse, ConfirmationPayload):
        data = {
            'TBK_PARAM': mock.Mock()
        }

        confirmation = Confirmation(self.commerce, self.request_ip, data)
        self.assertEqual(self.commerce, confirmation.commerce)
        self.assertEqual(self.request_ip, confirmation.request_ip)
        parse.assert_called_once_with(data['TBK_PARAM'])
        ConfirmationPayload.assert_called_once_with(parse.return_value)
        self.assertEqual(
            ConfirmationPayload.return_value, confirmation.payload)

    def test_init_wo_tbk_param(self):
        data = {}

        self.assertRaises(
            KeyError, Confirmation, self.commerce, self.request_ip, data)

    @mock.patch('tbk.webpay.confirmation.ConfirmationPayload')
    def test_parse(self, ConfirmationPayload):
        with open(os.path.join(os.path.dirname(__file__), 'fixtures', 'confirmation.txt')) as f:
            confirmation_data = f.read()
        data = {
            'TBK_PARAM': mock.Mock()
        }
        self.commerce.webpay_decrypt.return_value = (
            confirmation_data, "signature")

        confirmation = Confirmation(self.commerce, self.request_ip, data)

        params = CONFIRMATION_DATA.copy()
        params['TBK_MAC'] = "signature"

        self.commerce.webpay_decrypt.assert_called_once_with(data['TBK_PARAM'])
        ConfirmationPayload.assert_called_once_with(params)
        self.assertEqual(
            ConfirmationPayload.return_value, confirmation.payload)

    @mock.patch('tbk.webpay.confirmation.ConfirmationPayload')
    @mock.patch('tbk.webpay.confirmation.logger')
    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_is_success(self, parse, logger, ConfirmationPayload):
        parse.return_value = {
            'TBK_RESPUESTA': '0',
        }
        data = {
            'TBK_PARAM': mock.Mock()
        }
        payload = ConfirmationPayload.return_value
        payload.response = payload.SUCCESS_RESPONSE_CODE

        confirmation = Confirmation(self.commerce, self.request_ip, data)

        self.assertTrue(confirmation.is_success())

    @mock.patch('tbk.webpay.confirmation.ConfirmationPayload')
    @mock.patch('tbk.webpay.confirmation.logger')
    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_is_success_respuesta_not_0(self, parse, logger, ConfirmationPayload):
        data = {
            'TBK_PARAM': mock.Mock()
        }
        payload = ConfirmationPayload.return_value

        for i in range(1, 10):
            payload.response = -i
            confirmation = Confirmation(self.commerce, self.request_ip, data)
            self.assertFalse(confirmation.is_success())

    @mock.patch('tbk.webpay.confirmation.ConfirmationPayload')
    @mock.patch('tbk.webpay.confirmation.logger')
    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_order_id(self, parse, logger, ConfirmationPayload):

        data = {
            'TBK_PARAM': mock.Mock()
        }
        payload = ConfirmationPayload.return_value

        confirmation = Confirmation(self.commerce, self.request_ip, data)

        self.assertEqual(payload.order_id, confirmation.order_id)

    @mock.patch('tbk.webpay.confirmation.ConfirmationPayload')
    @mock.patch('tbk.webpay.confirmation.logger')
    @mock.patch('tbk.webpay.confirmation.Confirmation.parse')
    def test_amount(self, parse, logger, ConfirmationPayload):

        data = {
            'TBK_PARAM': mock.Mock()
        }
        payload = ConfirmationPayload.return_value

        confirmation = Confirmation(self.commerce, self.request_ip, data)

        self.assertEqual(payload.amount, confirmation.amount)


class ConfirmationPayloadTest(TestCase):

    def test_payload(self):
        payload = ConfirmationPayload(CONFIRMATION_DATA)

        self.assertEqual(payload.data, CONFIRMATION_DATA)

    def test_messages(self):
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
            self.assert_attribute(
                RESPONSE_CODES[i],
                'message',
                TBK_RESPUESTA=str(i)
            )

    def test_response(self):
        for i in range(0, -9):
            self.assert_attribute(
                i,
                'response',
                TBK_RESPUESTA=str(i)
            )

    def test_paid_at(self):
        santiago = pytz.timezone('America/Santiago')
        today = santiago.localize(datetime.datetime.today())
        today = today - datetime.timedelta(microseconds=today.microsecond)
        self.assert_attribute(
            today,
            'paid_at',
            TBK_FECHA_TRANSACCION=today.strftime("%m%d"),
            TBK_HORA_TRANSACCION=today.strftime("%H%M%S"),
        )

    def test_amount(self):
        self.assert_attribute(
            Decimal("12345.00"),
            'amount',
            TBK_MONTO='1234500'
        )

    def test_amount_decimals(self):
        self.assert_attribute(
            Decimal("12345.67"),
            'amount',
            TBK_MONTO='1234567'
        )

    def test_transaction_id(self):
        transaction_id = 1234500
        self.assert_attribute(
            transaction_id,
            'transaction_id',
            TBK_ID_TRANSACCION=str(transaction_id)
        )

    def test_order_id(self):
        orden_compra = '123aSd4500'
        self.assert_attribute(
            orden_compra,
            'order_id',
            TBK_ORDEN_COMPRA=orden_compra
        )

    def test_credit_card_last_digits(self):
        self.assert_attribute(
            '9509',
            'credit_card_last_digits',
            TBK_FINAL_NUMERO_TARJETA='9509'
        )

    def test_credit_card_number(self):
        self.assert_attribute(
            'XXXX-XXXX-XXXX-9509', 'credit_card_number',
            TBK_FINAL_NUMERO_TARJETA='9509'
        )

    def test_authorization_code(self):
        authorization_code = '000123456'
        self.assert_attribute(
            authorization_code,
            'authorization_code',
            TBK_CODIGO_AUTORIZACION=authorization_code
        )

    def test_accountable_date(self):
        santiago = pytz.timezone('America/Santiago')
        today = datetime.date.today()
        today = santiago.localize(
            datetime.datetime(today.year, today.month, today.day))
        self.assert_attribute(
            today,
            'accountable_date',
            TBK_FECHA_CONTABLE=today.strftime("%m%d"),
            TBK_FECHA_TRANSACCION=today.strftime("%m%d"),
            TBK_HORA_TRANSACCION=today.strftime("%H%M%S"),
        )

    def test_accountable_date_next_year(self):
        santiago = pytz.timezone('America/Santiago')
        transaction_date = datetime.datetime(2014, 12, 31, 11, 59, 59)
        accountable_date = datetime.datetime(2015, 01, 02)
        expected = santiago.localize(accountable_date)
        self.assert_attribute(
            expected,
            'accountable_date',
            TBK_FECHA_CONTABLE=accountable_date.strftime("%m%d"),
            TBK_FECHA_TRANSACCION=transaction_date.strftime("%m%d"),
            TBK_HORA_TRANSACCION=transaction_date.strftime("%H%M%S"),
        )

    def test_session_id(self):
        session_id = 'asdb1234asdQwe'
        self.assert_attribute(
            session_id,
            'session_id',
            TBK_ID_SESION=session_id
        )

    def test_session_id_null(self):
        self.assert_attribute(
            None,
            'session_id',
            TBK_ID_SESION="null"
        )

    def test_installments(self):
        for i in range(42):
            self.assert_attribute(
                i,
                'installments',
                TBK_NUMERO_CUOTAS=str(i)
            )

    def test_payment_type_code(self):
        for code in ("VN", "VC", "SI", "S2", "CI"):
            self.assert_attribute(
                code,
                'payment_type_code',
                TBK_TIPO_PAGO=code
            )

    def test_payment_type(self):
        PAYMENT_TYPES = {
            "VN": "Venta Normal",
            "VC": "Venta Cuotas",
            "SI": "Tres Cuotas Sin Interés",
            "S2": "Dos Cuotas Sin Interés",
            "CI": "Cuotas Comercio",
            "VD": "Redcompra",
        }
        for code in PAYMENT_TYPES.keys():
            self.assert_attribute(
                PAYMENT_TYPES[code],
                'payment_type',
                TBK_TIPO_PAGO=code
            )

    def test_get_item(self):
        payload = ConfirmationPayload(CONFIRMATION_DATA)
        for key, value in CONFIRMATION_DATA.items():
            self.assertEqual(value, payload[key])

    def assert_attribute(self, expected, attribute, **data):
        payload = ConfirmationPayload(data)

        self.assertEqual(expected, getattr(payload, attribute))

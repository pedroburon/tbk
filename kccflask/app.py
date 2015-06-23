import os

import requests
from flask import Flask, request, render_template

from tbk.webpay.commerce import Commerce
from tbk.webpay.payment import Payment
from tbk.webpay.logging import configure_logger
from tbk.webpay.logging.official import WebpayOfficialHandler

LOG_BASE_PATH = os.getenv('LOG_BASE_PATH', os.path.join(os.path.dirname(__file__), 'logs'))

RESULT_URL = os.getenv('RESULT_URL', 'http://127.0.0.1:5000/tbk_bp_resultado.cgi')
CONFIRMATION_URL = os.getenv('CONFIRMATION_URL', 'http://127.0.0.1:5000/confirm')

app = Flask(__name__)

commerce = Commerce.create_commerce()

logger = configure_logger(WebpayOfficialHandler(LOG_BASE_PATH, RESULT_URL))


def form_to_payment(form):
    payment = Payment(
        commerce=commerce,
        request_ip=request.remote_addr,
        success_url=form.get('TBK_URL_EXITO'),
        confirmation_url=RESULT_URL,
        failure_url=form.get('TBK_URL_FRACASO', form.get('TBK_URL_EXITO')),
        session_id=form.get('TBK_ID_SESION'),
        amount=form.get('TBK_MONTO'),
        order_id=form.get('TBK_ORDEN_COMPRA'),
    )
    return payment


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    if request.form:
        return "ACEPTADO"
    return "RECHAZADO"


@app.route("/tbk_bp_pago.cgi", methods=['GET', 'POST'])
def pago():
    if request.form:
        try:
            payment = form_to_payment(request.form)
            return payment.get_form()
        except:
            pass
    return Payment.ERROR_PAGE


@app.route("/tbk_bp_resultado.cgi", methods=['GET', 'POST'])
def resultado():
    if request.form:
        confirmation = Confirmation(request.form)
        response = requests.post(RESULT_URL, confirmation.payload.data)
        content = response.content
        if confirmation.is_success():
            if content == 'ACEPTADO':
                logger.confirmation(confirmation)
                return commerce.acknowledge
            logger.error(confirmation)
        else:
            logger.confirmation(confirmation)
    return commerce.reject


if __name__ == "__main__":
    app.run(debug=True)


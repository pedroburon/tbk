import os

import requests
from flask import Flask, request, render_template, redirect

from tbk.kcc import Commerce, Payment, Confirmation
from tbk.kcc.logging import configure_logger
from tbk.kcc.logging.official import WebpayOfficialHandler

LOG_BASE_PATH = os.getenv('LOG_BASE_PATH', os.path.join(os.path.dirname(__file__), 'logs'))

CONFIRMATION_URL = os.getenv('CONFIRMATION_URL')

VALIDATE_ORDER = os.getenv('VALIDATE_ORDER', 'True') == 'True'

app = Flask(__name__)

commerce = Commerce.create_commerce()

logger = configure_logger(WebpayOfficialHandler(LOG_BASE_PATH))


def form_to_payment(form):
    payment = Payment(
        commerce=commerce,
        request_ip=request.remote_addr,
        success_url=form.get('TBK_URL_EXITO'),
        confirmation_url=CONFIRMATION_URL,
        failure_url=form.get('TBK_URL_FRACASO', form.get('TBK_URL_EXITO')),
        session_id=form.get('TBK_ID_SESION'),
        amount=form.get('TBK_MONTO'),
        order_id=form.get('TBK_ORDEN_COMPRA'),
    )
    return payment

def validate_order(payload):
    return VALIDATE_ORDER

@app.route('/')
def index():
    return render_template('index.html')


@app.route("/tbk_bp_pago.cgi", methods=['GET', 'POST'])
def pago():
    if request.form:
        try:
            payment = form_to_payment(request.form)
            return redirect(payment.redirect_url)
        except Exception as e:
            print(e)
    return Payment.ERROR_PAGE


@app.route("/tbk_bp_resultado.cgi", methods=['GET', 'POST'])
def resultado():
    if request.form:
        confirmation = Confirmation(
            commerce=commerce,
            request_ip=request.remote_addr,
            data=request.form
        )
        return confirmation.get_webpay_response(validate_order)
    return commerce.reject


if __name__ == "__main__":
    app.run(debug=True)


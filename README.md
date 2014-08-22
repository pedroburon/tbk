tbk
===

[![Build Status](https://travis-ci.org/pedroburon/tbk.svg)](https://travis-ci.org/pedroburon/tbk)
[![Coverage Status](https://img.shields.io/coveralls/pedroburon/tbk.svg)](https://coveralls.io/r/pedroburon/tbk)

Python implementation of Transbank's Webpay protocol. A port from ruby implementation http://github.com/sagmor/tbk.

Currently trying to made this happen:

    payment = Payment(
        request_ip='123.123.123.123',
        commerce=mock.Mock(),
        success_url='http://localhost:8080/webpay/success/',
        confirmation_url='http://127.0.0.1:8080/webpay/confirmation/',
        failure_url='http://localhost:8080/webpay/failure/',
        session_id='SOME_SESSION_VALUE',
        amount=123456,
        order_id=1,
    )
    payment.redirect_url()

More info at http://github.com/sagmor/tbk

Install for development
-----------------------

After cloning the repo:

    python setup.py develop

For testing purposes:

    python setup.py test

Recommended:

    pip install nosy
    nosy

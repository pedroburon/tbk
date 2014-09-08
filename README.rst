tbk
===

|Build Status| |Coverage Status|

Python implementation of Transbank's Webpay protocol. A port from ruby
implementation http://github.com/sagmor/tbk.

.. raw:: html

   <!-- split here -->

Usage
-----

::

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

TODO: 

* *Fetch token* - Ready!
* Confirmation 
* Logging

About webpay communication protocol:
http://sagmor.com/rants/technical/webpay-communication-protocol/

Install for development
-----------------------

After cloning the repo:

::

    python setup.py develop

For testing purposes:

::

    python setup.py test

Recommended:

::

    pip install nosy
    nosy

.. |Build Status| image:: https://travis-ci.org/pedroburon/tbk.svg
   :target: https://travis-ci.org/pedroburon/tbk
.. |Coverage Status| image:: https://img.shields.io/coveralls/pedroburon/tbk.svg
   :target: https://coveralls.io/r/pedroburon/tbk

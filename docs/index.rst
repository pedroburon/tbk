tbk - Transbank's Webpay protocol
=================================

Python implementation of Transbank's Webpay protocol. `tbk` replaces **Webpay KCC** by a easy-to-use API.

Installation
------------

Install tbk by running::

    $ pip install tbk

Quick Start
-----------

Set environment variable for Commerce and initialize.

::

    os.environ['TBK_COMMERCE_ID'] = "597026007976"
    os.environ['TBK_COMMERCE_KEY'] = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAn3HzPC..."

    from tbk.webpay.commerce import Commerce

    commerce = Commerce.create_commerce()
    # for development purposes you can use
    # commerce = Commerce(testing=True)

If you want to set the official webpay log (for certification issues):

::

    from tbk.webpay.logging import configure_logger
    from tbk.webpay.logging.official import WebpayOfficialHandler

    configure_logger(WebpayOfficialHandler(LOG_BASE_PATH))
    # Others Handlers must implement `tbk.webpay.logging.BaseHandler`

Create a new payment and redirect user.

::

    from tbk.webpay.payment import Payment

    payment = Payment(
        request_ip=CUSTOMER_REQUEST_IP,
        commerce=commerce,
        success_url='http://localhost:8080/webpay/success/',
        confirmation_url='http://123.123.123.123:8080/webpay/confirmation/',
        failure_url='http://localhost:8080/webpay/failure/',
        session_id='SOME_SESSION_VALUE',
        amount=123456,
        order_id=1,
    )
    payment.redirect_url


Then to confirm payment, use an endpoint on confirmation_url` with:

::

    from tbk.webpay.confirmation import Confirmation

    def confirm_payment(request):
        confirmation = Confirmation(
            commerce=commerce,
            request_ip=request.ip_address,
            data=request.POST
        )

        # validate_confirmation validate if order_id and amount are valid.
        if confirmation.is_success() and validate_confirmation(confirmation.order_id, confirmation.amount):
            return HttpResponse(commerce.acknowledge)

        return HttpResponse(commerce.reject)


Index
--------

.. toctree::
   :maxdepth: 2

   api

* :ref:`genindex`
* :ref:`search`


Contribute
----------

- Issue Tracker: http://github.com/pedroburon/tbk/issues
- Source Code: http://github.com/pedroburon/tbk

Support
-------

If you are having issues, please let us know at http://github.com/pedroburon/tbk/issues.

License
-------

The project is licensed under the GPLv3 license.

tbk - Transbank's Webpay protocol
=================================

Python implementation of Transbank's Webpay protocol. `tbk` replaces **Webpay KCC** by a easy-to-use API.

Installation
------------

::

    pip install tbk



Quick Start
-----------

Set environment variable for Commerce and initialize.

::

    os.environ['TBK_COMMERCE_ID'] = "597026007976"
    os.environ['TBK_COMMERCE_KEY'] = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAn3HzPC1ZBzCO3edUCf/XJiwj3bzJpjjTi/zBO9O+DDzZCaMp...""

    from tbk.kcc import Commerce

    commerce = Commerce.create_commerce()
    # for development purposes you can use
    # commerce = Commerce(testing=True)

If you want to set the official webpay log (for certification issues):

::

    from tbk.kcc.logging import configure_logger
    from tbk.kcc.logging.official import WebpayOfficialHandler

    configure_logger(WebpayOfficialHandler(LOG_BASE_PATH), notification_url='http://127.0.0.1/notify')

Create a new payment and redirect user.

::

    from tbk.kcc import Payment

    def pay(request):
      payment = Payment(
          request_ip=request.remote_addr, # customer request ip
          commerce=commerce,
          success_url='http://example.net/success/',
          confirmation_url='http://123.123.123.123/webpay/confirm/', # callback url with IP
          failure_url='http://example.net/webpay/failure/',
          session_id='SOME_SESSION_VALUE',
          amount=123456, # could be int, str or Decimal
          order_id="oc123",
      )
      return redirect(payment.redirect_url, status_code=302)


Then to confirm payment, use an endpoint with:

::

    from tbk.kcc import Confirmation

    def confirm_payment(request):
        confirmation = Confirmation(
            commerce=commerce,
            request_ip=request.remote_addr,
            data=request.form
        )

        def validate_order(payload):
            order = Order.get_order(id=payload.order_id, amount=payload.amount)
            if order:
              order.set_paid()
              return True
            return False

        return HttpResponse(confirmation.get_webpay_response(validate_order))


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

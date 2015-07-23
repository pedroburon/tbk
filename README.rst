tbk - Transbank's Webpay protocol
=================================

Python implementation of Transbank's Webpay protocol.


|Latest Version| |Development Status| |Build Status| |Coverage Status| |Code Health| |Downloads| |Documentation|


.. |Latest Version| image:: https://pypip.in/version/tbk/badge.svg?
    :target: https://pypi.python.org/pypi/tbk/
    :alt: Latest Version
.. |Development Status| image:: https://pypip.in/status/tbk/badge.svg?
   :target: https://pypi.python.org/pypi/tbk/
   :alt: Development Status
.. |Build Status| image:: https://travis-ci.org/pedroburon/tbk.svg?
   :target: https://travis-ci.org/pedroburon/tbk
   :alt: Build Status
.. |Coverage Status| image:: https://img.shields.io/coveralls/pedroburon/tbk.svg?
   :target: https://coveralls.io/r/pedroburon/tbk
   :alt: Coverage Status
.. |Code Health| image:: https://landscape.io/github/pedroburon/tbk/master/landscape.svg?
   :target: https://landscape.io/github/pedroburon/tbk/master
   :alt: Code Health
.. |Downloads| image:: https://pypip.in/download/tbk/badge.svg?period=month
   :target: https://pypi.python.org/pypi/tbk/
   :alt: Downloads
.. |Documentation| image:: https://readthedocs.org/projects/tbk/badge/?version=latest
   :target: https://readthedocs.org/projects/tbk/?badge=latest
   :alt: Documentation Status

Installation
------------

::

    pip install tbk


Usage
-----

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

About webpay communication protocol: http://sagmor.com/rants/technical/webpay-communication-protocol/

.. split here

Changelog
---------

* Transbank certification achieved!
* New confirmation method get_webpay_response 
* Logs with real url
* New logger error method

Development
-----------

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

Credits
-------

This is a port from ruby implementation http://github.com/sagmor/tbk.

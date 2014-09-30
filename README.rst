tbk - Transbank's Webpay protocol
=================================

**Attention: Beta not ready for production**

Python implementation of Transbank's Webpay protocol. A port from ruby
implementation http://github.com/sagmor/tbk.


|Build Status| |Coverage Status|

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

    from tbk.webpay.commerce import Commerce        
    commerce = Commerce.create_commerce()

If you want to set the official webpay log (for certification issues):

::

    from tbk.webpay.logging import configure_logger
    from tbk.webpay.logging.official import WebpayOfficialHandler

    configure_logger(WebpayOfficialHandler(LOG_BASE_PATH))

Create a new payment and redirect user.

::

    
    from tbk.webpay.payment import Payment

    payment = Payment(
        request_ip='123.123.123.123',
        commerce=commerce,
        success_url='http://localhost:8080/webpay/success/',
        confirmation_url='http://127.0.0.1:8080/webpay/confirmation/',
        failure_url='http://localhost:8080/webpay/failure/',
        session_id='SOME_SESSION_VALUE',
        amount=123456,
        order_id=1,
    )
    payment.redirect_url
    
    
Then to confirm payment, use an endpoint with:

::

    from tbk.webpay.confirmation import Confirmation

    def confirmation(request):
        conf = Confirmation(
            commerce=commerce,
            request_ip=request.ip_address,
            data=request.POST
        )
        
        if validate_confirmation(conf) or not conf.is_success() :
            return HttpResponse(conf.reject)
        
        return HttpResponse(conf.acknowledge)


More info at http://github.com/sagmor/tbk

.. split here

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


About webpay communication protocol:
http://sagmor.com/rants/technical/webpay-communication-protocol/





.. |Build Status| image:: https://travis-ci.org/pedroburon/tbk.svg
   :target: https://travis-ci.org/pedroburon/tbk
.. |Coverage Status| image:: https://img.shields.io/coveralls/pedroburon/tbk.svg
   :target: https://coveralls.io/r/pedroburon/tbk



__all__ = ['WebpayLogger', 'logger']


class WebpayLogger(object):
    def payment(self, payment):
        pass  # pragma: no cover

    def confirmation(self, confirmation):
        pass  # pragma: no cover


logger = WebpayLogger()

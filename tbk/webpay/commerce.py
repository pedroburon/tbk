import os

from six.moves.urllib.parse import urlparse

from .encryption import Encryption, Decryption

from Crypto.PublicKey import RSA

__all__ = ['Commerce']


TEST_COMMERCE_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAn3HzPC1ZBzCO3edUCf/XJiwj3bzJpjjTi/zBO9O+DDzZCaMp
14aspxQryvJhv8644E19Q+NHfxtz1cxd2wnSYKvay1gJx30ZlTOAkzUj4QMimR16
vomLlQ3T2MAz1znt/PVPVU7T/JOG9R+EbiHNVKa/hUjwJEFVXLQNME97nHoLjb3v
V5yV2aVhmox7b54n6F3UVPHvCsHKbJpXpE+vnLpVmdETbNpFVrDygXyG+mnEvyiO
BLIwEY3XTMrgXvS069groLi5Gg8C5LDaYOWjE9084T4fiWGrHhn2781R1rykunTu
77wiWPuQHMS0+YC7mhnsk8Z/ilD+aWz/vhsgHwIDAQABAoIBAQCM+Nrt4cpNKQmn
+Ne8348CGRS9ACXp6WRg6OCQXO4zM7lRZAminVgZgSQXE6aJR+T9rIWMeG7GWydX
aJGzEEQJZOjV0MkUr+7mk9qiTOGkGHmGlyHnRQU8jDU59vXe3UEl3l5+NmwHbQht
waf9F7XLmoLK/WoVJA6tICRpCl1oQrpziqN+gjdmMpz9i8I1sMFE7+Y7xf+7S2u7
c1MRPUWqgdS9yViQVh3vZi25m5CyKRVnOB0hpNuZ7nrJymtADYSWt9wV2W1fX+MX
UUoYfxyQQvWryHhGdedU7GGAnoEdblUcDkBuAaFmsm1P8K4HQZLWP4v6pYlW2JLa
Zoaerb3BAoGBANCRevl0CLB0HBU7sCs0eN9fTkIEsh3OVIxPSBqDnKsynJrIWovK
cs37Vb6phzdQO3ADoFJvR9ck8+v6Cv0KR8IOFl9wfC4ZoxkKBBeq94ZLN+YhE2PW
KiRFybqcgCtzxKS3MyWgpIcT9xFtHVjlorZ8Jk51fgLZbGzamtLhderVAoGBAMO0
mIiiV4l2vXzu4tFfkpu/GOx/D9/vAic3X9FOky09BNCyuMXMQgI8e3wWsGEZghls
Vg9KDV5EPxAmpumcdPFK2IMACaH41ac7vys3ZD8kMK0INQkuDAcG4YsxMaTwEPo0
p1i3zwwEWwknw1yJkOyozz0EcIzS9NrZZEjnBHEjAoGAQ81XdeqzvHEyg/CQd6sq
NCtubGXMZYYi1C4d2Yi5kKn2YRcK4HDi23V+TWodK+0oNWToZIQKjbVUmn0Bv3rt
EvezbDlMFUx+SfCIng0VRJIFTQmpnQYNUxdg2gpwXC/ZWFa6CNxtQABMjFy1cqXM
PJild1IYseJurgBu3mkvBTUCgYBqA/T1X2woLUis2wPIBAv5juXDh3lkB6eU8uxX
CEe2I+3t2EM781B2wajrKadWkmjluMhN9AGV5UZ8S1P0DStUYwUywdx1/8RNmZIP
qSwHAGXV9jI0zNr7G4Em0/leriWkRM26w6fHjLx8EyxDfsohSbkqBrOptcWqoEUx
MOQ5HQKBgAS4sbddOas2MapuhKU2surEb3Kz3RCIpta4bXgTQMt9wawcZSSpvnfT
zs5sehYvBFszL3MV98Uc50HXMf7gykRCmPRmB9S+f+kiVRvQDHfc9nRNg2XgcotU
KAE16PQM8GihQ0C+EcXHouyud5CRJGfyurokRlH/jY3BiRAG5c+6
-----END RSA PRIVATE KEY-----
""".strip()

TEST_WEBPAY_KEY = """
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAtKe3HHWwRcizAfkbS92V
fQr8cUb94TRjQPzNTqBduvvj65AD5J98Cn1htE3NzOz+PjPRcnfVe53V4f3+YlIb
6nnxyeuYLByiwoPkCmpOFBxNp04/Yh3dxN4xgOANXA37rNbDeO4WIEMG6zbdQMNJ
7RqQUlJSmui8gt3YxtqWBhBVW79qDCYVzxFrv3SH7pRuYEr+cxDvzRylxnJgr6ee
N7gmjoSMqF16f9aGdQ12obzV0A35BqpN6pRFoS/NvICbEeedS9g5gyUHf54a+juB
OV2HH5VJsCCgcb7I7Sio/xXTyP+QjIGJfpukkE8F+ohwRiChZ9jMXofPtuZYZiFQ
/gX08s5Qdpaph65UINP7crYbzpVJdrT2J0etyMcZbEanEkoX8YakLEBpPhyyR7mC
73fWd9sTuBEkG6kzCuG2JAyo6V8eyISnlKDEVd+/6G/Zpb5cUdBCERTYz5gvNoZN
zkuq4isiXh5MOLGs91H8ermuhdQe/lqvXf8Op/EYrAuxcdrZK0orI4LbPdUrC0Jc
Fl02qgXRrSpXo72anOlFc9P0blD4CMevW2+1wvIPA0DaJPsTnwBWOUqcfa7GAFH5
KGs3zCiZ5YTLDlnaps8koSssTVRi7LVT8HhiC5mjBklxmZjBv6ckgQeFWgp18kuU
ve5Elj5HSV7x2PCz8RKB4XcCAwEAAQ==
-----END PUBLIC KEY-----
""".strip()

WEBPAY_KEY = """
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAxKKjroxE7X44TQovh9A9
ZpntP7LrdoyFsnJbDKjOOCoiid92FydN5qemyQCeXhsc7QHUXwGdth22fB8xJr3a
MZBEUJ+BKFrL+W6yE5V+F5Bj0Uq3lL0QMAIftGhLpgqw0ZMtU89kyd9Q4Rclq4r8
p2m/ZD7Pn5EmTOFSeyoWTMZQDl7OEoCKh/cZH5NJdWL08lCI+sGLOghRmFzkve4h
F9JCwKA7NYG7j3BWh39Oj2NIXEY/TO1Y3Y2WfNv9nvTpr46SpFlyp0KOhSiqgvXX
DgeXlebyqS82ch2DzOV9fjDAw7t71WXJBAev8Gd6HXwIXE/JP6AnLCa2Y+b6Wv8K
GWBCMIBXWL0m7WHeCaJ9Hx2yXZmHJh8FgeKffFKCwn3X90JiMocOSGsOE+Sfo85S
h/39Vc7vZS3i7kJDDoz9ab9/vFy30RuJf4p8Erh7kWtERVoG6/EhR+j4N3mgIOBZ
SHfzDAoOnqP5l7t2RXYcEbRLVN6o+XgUtalX33EJxJRsXoz9a6PxYlesIwPbKteD
BZ/xyJDwTc2gU2YzSH8G9anKrcvITBDULSAuxQUkYOiLbkb7vSKWDYKe0do6ibO3
RY/KXI63Q7bGKYaI2aa/8GnqVJ2G1U2s59NpqX0aaWjn59gsA8trA0YKOZP4xJIh
CvLM94G4V7lxe2IHKPqLscMCAwEAAQ==
-----END PUBLIC KEY-----
""".strip()


class Commerce(object):
    TEST_COMMERCE_KEY = TEST_COMMERCE_KEY
    TEST_COMMERCE_ID = "597026007976"

    webpay_key_id = 101

    def __init__(self, id=None, key=None, testing=False):
        self.testing = testing
        self.id = self.__get_id(id)
        self.key = self.__get_key(key)

    @staticmethod
    def create_commerce():
        """
        Creates commerce from environment variables.
        """
        commerce_id = os.getenv('TBK_COMMERCE_ID')
        commerce_key = os.getenv('TBK_COMMERCE_KEY')
        commerce_testing = os.getenv('TBK_COMMERCE_TESTING') == 'True'

        if not commerce_testing:
            if commerce_id is None:
                raise ValueError("create_commerce needs TBK_COMMERCE_ID environment variable")
            if commerce_key is None:
                raise ValueError("create_commerce needs TBK_COMMERCE_KEY environment variable")

        return Commerce(
            id=commerce_id or Commerce.TEST_COMMERCE_ID,
            key=commerce_key,
            testing=commerce_testing
        )

    def __get_key(self, key):
        if not key:
            if self.testing:
                return self.TEST_COMMERCE_KEY
            raise TypeError("Commerce needs a key")
        return key

    def __get_id(self, id):
        if not id:
            if self.testing:
                return self.TEST_COMMERCE_ID
            raise TypeError("Commerce needs an id")
        return id

    def webpay_decrypt(self, encrypted):
        commerce_key = self.get_commerce_key()
        webpay_key = self.get_webpay_key()
        decryption = Decryption(commerce_key, webpay_key)
        decrypted = decryption.decrypt(encrypted)
        return decrypted

    def webpay_encrypt(self, decrypted):
        commerce_key = self.get_commerce_key()
        webpay_key = self.get_webpay_key()
        encryption = Encryption(commerce_key, webpay_key)
        return encryption.encrypt(decrypted)

    def get_webpay_key(self):
        return RSA.importKey(TEST_WEBPAY_KEY if self.testing else WEBPAY_KEY)

    def get_commerce_key(self):
        return RSA.importKey(self.key)

    def get_public_key(self):
        return self.get_commerce_key().publickey().exportKey()

    def get_config_tbk(self, confirmation_url):
        config = (
            "IDCOMERCIO = {commerce_id}\n"
            "MEDCOM = 1\n"
            "TBK_KEY_ID = 101\n"
            "PARAMVERIFCOM = 1\n"
            "URLCGICOM = {confirmation_path}\n"
            "SERVERCOM = {confirmation_host}\n"
            "PORTCOM = {confirmation_port}\n"
            "WHITELISTCOM = ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz 0123456789./:=&?_\n"
            "HOST = {confirmation_host}\n"
            "WPORT = {confirmation_port}\n"
            "URLCGITRA = /filtroUnificado/bp_revision.cgi\n"
            "URLCGIMEDTRA = /filtroUnificado/bp_validacion.cgi\n"
            "SERVERTRA = {webpay_server}\n"
            "PORTTRA = {webpay_port}\n"
            "PREFIJO_CONF_TR = HTML_\n"
            "HTML_TR_NORMAL = http://127.0.0.1/notify\n"
        )
        confirmation_uri = urlparse(confirmation_url)
        webpay_server = "https://certificacion.webpay.cl" if self.testing else "https://webpay.transbank.cl"
        webpay_port = 6443 if self.testing else 443
        return config.format(commerce_id=self.id,
                             confirmation_path=confirmation_uri.path,
                             confirmation_host=confirmation_uri.hostname,
                             confirmation_port=confirmation_uri.port,
                             webpay_port=webpay_port,
                             webpay_server=webpay_server)

    @property
    def acknowledge(self):
        return self.webpay_encrypt('ACK')

    @property
    def reject(self):
        return self.webpay_encrypt('ERR')

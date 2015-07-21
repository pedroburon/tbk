
import hashlib
import collections


class Params(collections.OrderedDict):
    fields = []
    optionals = ['TBK_MAC']

    def __init__(self, *args, **kwargs):
        try:
            self.commerce = kwargs.pop('commerce')
        except KeyError:
            raise TypeError('Must create {class_name} with Commerce instance.'.format(class_name=self.__class__.__name__))
        super(Params, self).__init__(*args, **kwargs)

    def validate(self):
        if self.fields:
            for field in self.fields:
                if field not in self.keys():
                    raise self.KeyExpected(field)

    def get_raw(self):
        pairs = map(lambda pair: "{pair[0]}={pair[1]}".format(pair=pair), self.get_pairs())
        return "#".join(pairs)

    def get_encrypted(self):
        return self.commerce.webpay_encrypt(self.get_raw())

    def clean_TBK_MAC(self, _):
        pairs = self.get_pairs(exclude=['TBK_MAC'])
        pairs = map(lambda pair: "{pair[0]}={pair[1]}".format(pair=pair), pairs)
        hashable = "&".join(pairs).encode('utf-8')
        hash = hashlib.new('md5')
        hash.update(hashable)
        hash.update(self.commerce.id.encode('utf-8'))
        hash.update(b'webpay')
        return hash.hexdigest()

    def get_pairs(self, exclude=None):
        exclude = exclude or []
        pairs = []
        keys = self.fields or self.keys()
        for key in keys:
            if key in exclude:
                continue
            value = self.get(key)
            try:
                cleaner = getattr(self, 'clean_' + key)
                value = cleaner(value)
            except AttributeError as e:
                pass
            except Params.DontUseParam:
                continue

            if value is None:
                if key not in self.optionals:
                    raise self.KeyExpected(key)
            else:
                pairs.append((key, value))
        return pairs

    class DontUseParam(Exception):
        pass


    class KeyExpected(Exception):
        pass

import functools

class key:
    def __init__(self, k, h):
        self.k, self.h = k, h

    def __call__(self, f):
        setattr(f, "_key", (self.k, self.h))
        return f


def mouse():
    pass


class InputMeta(type):
    def __new__(cls, name, parents, dct):
        c = super(InputMeta, cls).__new__(cls, name, parents, dct)
        c.set_keys(dct)
        return c


class Input(object):
    __metaclass__ = InputMeta
    @classmethod
    def set_keys(klass, dct):
        klass.keys = {}
        for k, v in dct.items():
            if hasattr(v, "_key"):
                klass.keys[k] = v._key
                print v._key, k


class InputChain:
    pass


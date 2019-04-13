
def m6(self, **word):
    print("m6 oword", word)


def m10(self, **word):
    print("m10 oword", word)


def m11(self, **word):
    print("m11 oword", word)


def m12(self, **word):
    print("m12 oword", word)


def on_abort(self, *args, **kwargs):
    print(args, kwargs)
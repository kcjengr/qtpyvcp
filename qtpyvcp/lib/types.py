class DotDict(dict):
    """Simple dot.notation access for dictionary values"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
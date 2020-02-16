
from qtpyvcp import KEYBOARDS


def getKeyboard(vkb_name, fallback='default'):
    try:
        return KEYBOARDS[vkb_name]
    except KeyError:
        default = KEYBOARDS['default']
        return KEYBOARDS.get(fallback, default)

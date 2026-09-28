from PySide6.QtCore import QEnum
from enum import Enum

TYPE_MAP = {
    0: 'bool',
    1: 'uint',
    2: 'sint',
    3: 'real',
    'bool': 0,
    'uint': 1,
    'sint': 2,
    'real': 3,
    }


@QEnum
class HalType(Enum):
    bool = 0
    usint = 1
    sint = 2
    real = 3

    def toString(self, typ):
        return TYPE_MAP[typ]

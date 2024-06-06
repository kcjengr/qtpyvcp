from PySide6.QtCore import QEnum
from enum import Enum

TYPE_MAP = {
    0: 'bit',
    1: 'u32',
    2: 's32',
    3: 'float',
    'bit': 0,
    'u32': 1,
    's32': 2,
    'float': 3,
    }


@QEnum
class HalType(Enum):
    bit = 0
    u32 = 1
    s32 = 2
    float = 3

    def toString(self, typ):
        return TYPE_MAP[typ]

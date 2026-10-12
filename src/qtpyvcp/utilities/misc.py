import os
import math
import locale
import re


def cnc_float(value):
    """
    Parse a float value with CNC decimal point format (e.g., "1234.5678")
    
    This function ensures that CNC decimal values are always parsed correctly 
    regardless of system locale. It temporarily switches to C locale for parsing 
    to avoid locale-dependent float() behavior, which is critical for CNC 
    applications where decimal point (.) must always be used consistently.
    
    Args:
        value: String or numeric value to convert to float
        
    Returns:
        float: The parsed value
        
    Raises:
        ValueError: If the value cannot be parsed as a CNC decimal number
        TypeError: If the value is not a valid type for conversion
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        raise ValueError(f"Cannot convert {type(value).__name__} to CNC float")
    
    value = value.strip()
    if not value:
        return 0.0
    
    # Save current locale
    current_locale = locale.getlocale(locale.LC_NUMERIC)
    
    try:
        # Temporarily set C locale for CNC-standard parsing
        locale.setlocale(locale.LC_NUMERIC, 'C')
        result = float(value)
        return result
    except (ValueError, locale.Error) as e:
        raise ValueError(f"Invalid CNC decimal format: '{value}'. Use format like 1234.5678")
    finally:
        # Restore original locale
        try:
            if current_locale[0] is not None:
                locale.setlocale(locale.LC_NUMERIC, current_locale)
        except locale.Error:
            # If restore fails, ensure we're at least in a known state
            locale.setlocale(locale.LC_NUMERIC, 'C')

# Characters a numeric entry field accepts while it is being typed into:
# digits, a decimal point, an exponent, the four arithmetic operators, power
# (** or ^), parentheses, spaces and "=" (a leading "=", or -= and the like
# for an entry that works on the current value). Anything else is refused at
# the keyboard, the way a plain number field refuses letters.
CNC_EXPRESSION_PATTERN = r'^[0-9.eE+\-*/^()\s=]*$'

# The same, for a field that also takes a unit after a number: the letters
# of mm, cm, m, in and ft, plus " for inches and ' for feet.
CNC_UNIT_EXPRESSION_PATTERN = r'^[0-9.eE+\-*/^()\s=mcinft"\']*$'

# Longest expression cnc_eval will parse. Arithmetic typed into a field is a
# few dozen characters at most.
_CNC_EXPRESSION_MAX_LENGTH = 200

# Deepest bracket nesting cnc_eval will parse. Far beyond any real entry, and
# keeps the recursive parser well clear of Python's recursion limit.
_CNC_MAX_NESTING = 20


# Every unit a number can be typed in, as its length in metres. Surface
# speed, feeds per rev and feeds per minute are all a length over a
# denominator both systems share (/min, /rev), so converting any of them is
# only the ratio of two of these lengths: 600ft typed into a field whose
# base unit is m (per minute) is 600 * 0.3048 / 1.0.
CNC_UNITS_IN_METRES = {
    'mm': 0.001,
    'cm': 0.01,
    'm': 1.0,
    'in': 0.0254,
    '"': 0.0254,
    'ft': 0.3048,
    "'": 0.3048,
}

# One token of an entry, tried in this order at each position:
#   mixed     1 1/2 -- a whole number, a space, a fraction
#   fraction  5/8 when the inch or foot mark follows. The marks are the
#             imperial shorthand and read the way a drawing is written: 5/8"
#             is five eighths of an inch as one quantity. The spelled-out
#             units follow the ordinary rule instead, so 3/4 in is 3 divided
#             by 4 inches -- which is not a length, and is refused.
#   number    12, 1.5, .5, 1e-3
#   unit      mm cm in ft m " ' -- longer names first so mm is not read as m
#   op        + - * / ( ) and power, ** or ^
_CNC_TOKEN = re.compile(r'''\s*(?:
      (?P<mixed>\d+\s+\d+/\d+)(?![\d./])
    | (?P<fraction>\d+/\d+)(?=\s*["'])
    | (?P<number>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)
    | (?P<unit>mm|cm|in|ft|m|"|')(?![A-Za-z])
    | (?P<op>\*\*|[-+*/()^])
    )''', re.VERBOSE)


def _cnc_tokens(text, value):
    """Split an entry into (kind, text) tokens, or raise ValueError."""
    tokens = []
    pos = 0
    text = text.rstrip()
    while pos < len(text):
        match = _CNC_TOKEN.match(text, pos)
        if match is None:
            raise ValueError(f"Invalid number or expression: '{value}'")
        kind = match.lastgroup
        text_ = match.group(kind)
        # ^ is power, the way it is written on paper -- not bitwise XOR
        tokens.append((kind, '**' if text_ == '^' else text_))
        pos = match.end()
    return tokens


def _cnc_same(a, b):
    """Two length powers are the same. Powers can be fractional part way
    through an entry -- (3in**2 + 4in**2)**0.5 goes through an area -- so
    they are compared with a tolerance."""
    return abs(a - b) < 1e-9


def _cnc_power(base, exponent, value):
    try:
        result = base ** exponent
    except ZeroDivisionError:
        raise ValueError(f"Division by zero in '{value}'")
    except OverflowError:
        raise ValueError(f"Expression does not give a finite number: '{value}'")
    if isinstance(result, complex):
        # (-8)**(1/3): no real answer
        raise ValueError(f"Invalid number or expression: '{value}'")
    return result


def _cnc_evaluate(tokens, value, base_unit):
    """Work out a tokenised entry, keeping track of what kind of quantity
    every part of it is.

    Each part is a (number, length power) pair: power 0 is a plain number,
    1 a length, -1 "per length", 2 an area. A unit makes its number a length
    in base_unit. Multiplying adds the powers and dividing subtracts them, so
    3/4in is 3 divided by a length -- power -1 -- and is refused, where 10in/4
    is a length. Adding needs matching powers, except that a plain number
    added to a length is taken to be in base_unit (2in + 3 is 2 in + 3 mm in
    a mm field). The answer must be a length or a plain number; a plain
    number is in base_unit. Without base_unit no unit is allowed at all.
    """
    base = CNC_UNITS_IN_METRES[base_unit] if base_unit else None
    position = [0]
    depth = [0]

    def invalid():
        return ValueError(f"Invalid number or expression: '{value}'")

    def peek(offset=0):
        index = position[0] + offset
        return tokens[index] if index < len(tokens) else (None, None)

    def take():
        token = peek()
        position[0] += 1
        return token

    def fraction(text):
        numerator, denominator = (int(part) for part in text.split('/'))
        if denominator == 0:
            raise ValueError(f"Division by zero in '{value}'")
        return numerator / denominator

    def mixed(text):
        whole, fraction_part = text.split()
        numerator, denominator = (int(part) for part in fraction_part.split('/'))
        # 1 5/4 is not how a mixed number is written; it is almost certainly
        # a typo for 1 1/4 or 1 3/4, so it is refused, not guessed at.
        if denominator == 0 or numerator >= denominator:
            raise invalid()
        return int(whole) + numerator / denominator

    def with_unit(number):
        """number followed by a unit token: a length in base_unit."""
        unit = take()[1]
        if base is None:
            raise invalid()
        quantity = number * CNC_UNITS_IN_METRES[unit] / base
        if unit == "'":
            quantity += inches_after_feet()
        return (quantity, 1)

    def inches_after_feet():
        """The 6" of 1'6" -- inches written straight after feet add to them."""
        kind, text = peek()
        if kind == 'fraction' and peek(1) == ('unit', '"'):
            number = fraction(take()[1])
        elif kind in ('number', 'mixed') and peek(1) == ('unit', '"'):
            number = float(take()[1]) if kind == 'number' else mixed(take()[1])
        else:
            return 0.0
        take()  # the "
        return number * CNC_UNITS_IN_METRES['"'] / base

    def primary():
        kind, text = take()
        if kind == 'op' and text == '(':
            depth[0] += 1
            if depth[0] > _CNC_MAX_NESTING:
                raise invalid()
            inner = expression()
            if take() != ('op', ')'):
                raise invalid()
            depth[0] -= 1
            # (3/4)in: a unit goes on a number, not on a bracket
            if peek()[0] == 'unit':
                raise invalid()
            return inner
        if kind == 'fraction':
            # 5/8" -- the fraction and its mark are one quantity
            return with_unit(fraction(text))
        if kind in ('number', 'mixed'):
            number = float(text) if kind == 'number' else mixed(text)
            if peek()[0] == 'unit':
                return with_unit(number)
            return (number, 0)
        raise invalid()

    def unary():
        if peek() in (('op', '-'), ('op', '+')):
            sign = take()[1]
            number, power = unary()
            return (-number if sign == '-' else number, power)
        return exponent()

    def exponent():
        """a ** b. It binds tighter than a leading minus (-2**2 is -4) and
        works right to left (2**3**2 is 2**9). The exponent must be a plain
        number; a length to a power is that power of a length (an area for
        2), which is refused at the end unless it comes back to a length."""
        number, power = primary()
        if peek() == ('op', '**'):
            take()
            right, right_power = unary()
            if not _cnc_same(right_power, 0):
                raise invalid()
            number, power = _cnc_power(number, right, value), power * right
        return (number, power)

    def term():
        number, power = unary()
        while peek() in (('op', '*'), ('op', '/')):
            operator_ = take()[1]
            right, right_power = unary()
            if operator_ == '*':
                number, power = number * right, power + right_power
            else:
                if right == 0.0:
                    raise ValueError(f"Division by zero in '{value}'")
                number, power = number / right, power - right_power
        return (number, power)

    def expression():
        number, power = term()
        while peek() in (('op', '+'), ('op', '-')):
            sign = take()[1]
            right, right_power = term()
            # A plain number added to a length is in base_unit
            if ((_cnc_same(power, 0) and _cnc_same(right_power, 1))
                    or (_cnc_same(power, 1) and _cnc_same(right_power, 0))):
                power = right_power = 1
            if not _cnc_same(power, right_power):
                raise invalid()
            number = number + right if sign == '+' else number - right
        return (number, power)

    number, power = expression()
    if position[0] != len(tokens):
        raise invalid()
    return number, power


# An entry that works on the field's current value: +5 adds, -=5 subtracts,
# *2, /2, ^2 (or **2), and a lone - flips the sign. A - followed by a number
# is a negative number, not a subtraction -- that needs -=. The = is optional
# after the other operators (+=5, *=2).
_CNC_RELATIVE = re.compile(r'^\s*(\*\*|\^|\+|\*|/|-(?==))=?(.*)$', re.DOTALL)


def _cnc_relative(value, base_unit, current):
    """Work out a relative entry against current, or return None if value
    is not one.

    current is in base_unit when the field has one (a length), a plain
    number otherwise, and the answer has to stay that kind of quantity:
    +1in adds an inch to a length, but /2in or ^2 on a length is refused.
    """
    text = value.strip()
    current = float(current)
    if text == '-':
        return -current
    match = _CNC_RELATIVE.match(text)
    if match is None:
        return None
    operator_, rest = match.group(1), match.group(2).strip()
    if not rest:
        raise ValueError(f"Invalid number or expression: '{value}'")
    if len(rest) > _CNC_EXPRESSION_MAX_LENGTH:
        raise ValueError(f"Invalid number or expression: '{value}'")

    current_power = 1 if base_unit else 0
    number, power = _cnc_evaluate(_cnc_tokens(rest, value), value, base_unit)

    if operator_ in ('+', '-'):
        # A plain number added to a length is in base_unit
        if current_power == 1 and _cnc_same(power, 0):
            power = 1
        if not _cnc_same(power, current_power):
            raise ValueError(f"'{value}' is not a length")
        return current + number if operator_ == '+' else current - number

    # * / and power take a plain number
    if not _cnc_same(power, 0):
        raise ValueError(f"Invalid number or expression: '{value}'")
    if operator_ == '*':
        return current * number
    if operator_ == '/':
        if number == 0.0:
            raise ValueError(f"Division by zero in '{value}'")
        return current / number
    if not _cnc_same(current_power * number, current_power):
        # a length squared is an area
        raise ValueError(f"'{value}' is not a length")
    return _cnc_power(current, number, value)


def cnc_eval(value, base_unit=None, current=None, rounded=True):
    """
    Parse a number the way cnc_float does, or evaluate simple arithmetic.

    Lets an operator type the sum instead of working it out first:
    ``1.4*25.4`` gives 35.56, ``3/4`` gives 0.75, ``(50-12)/2`` gives 19.0.
    A mixed number is written with a space, ``1 1/2`` = 1.5; a dash is a
    minus, so ``1-1/2`` = 0.5. A plain number is handed straight to
    cnc_float, so it parses exactly as it always has.

    With ``base_unit`` set, a number may also carry a unit -- mm, cm, m, in
    or ", ft or ' -- and is converted into ``base_unit``: ``38mm`` in an
    inch field gives 1.4961, ``600ft`` in a surface-speed field whose base is
    m (per minute) gives 182.88. The rules:

    * a unit belongs to the number right before it: ``10in/4`` = 63.5 mm,
      and ``3/4in`` is 3 divided by 4 inches
    * the answer must be a length, so ``3/4in`` and ``1in*2in`` are refused
    * a bare number is in ``base_unit``, also when added to a length:
      ``2in + 3`` in a mm field is 53.8
    * a mixed number takes a unit as a whole: ``1 3/4 in`` = 44.45 mm, and
      its fraction must be below 1
    * a whole-number fraction before " or ' is one quantity, of any size:
      ``5/8"`` = 15.875 mm, ``5/4'`` = 381 mm
    * ' works like ": ``1.5'`` and ``1 1/2'`` are feet
    * inches straight after feet add to them: ``1'6"`` = 457.2 mm
    * a unit cannot follow a bracket: ``(3/4)in`` is refused

    Without ``base_unit`` a unit is an error, so a field that has none, such
    as an RPM or a tool number, refuses one.

    Power is ``**`` or ``^``: ``2^3`` = 8. The exponent must be a plain
    number; ``((3in)^2 + (4in)^2)^0.5`` is 5 in.

    With ``current`` given -- the field's actual value, never its rounded
    display -- an entry can work on it: ``+5`` adds 5, ``-=5`` subtracts,
    ``*2``, ``/2``, ``^2``, and ``-`` alone flips the sign. ``-5`` is still
    the number -5. On a length, ``+1in`` adds an inch; multiplying, dividing
    and power take plain numbers only.

    Only numbers, units, ``+ - * /``, parentheses and a leading sign are
    allowed, optionally after a leading ``=``. The entry is split into those
    tokens and worked out by a small parser -- nothing is ever passed to
    eval(), so names, calls and attribute access are rejected, not run.

    Args:
        value: A number, or a string holding a number or an expression.
        base_unit: The unit the field holds its value in (a key of
            CNC_UNITS_IN_METRES), or None for a field without units.
        current: The field's current value, for an entry that works on it
            (+5, /2 ...), or None if there is none.
        rounded: Round the answer to 10 decimals (below any machine's
            resolution, and it turns 35.559999999999995 back into 35.56). A
            caller that converts the answer into other units passes False and
            rounds once afterwards, so the rounding does not stack.

    Returns:
        float: The value.

    Raises:
        ValueError: If the text is neither a number nor an allowed
            expression, divides by zero, is not a length, or does not give
            a finite number.
    """
    if base_unit and base_unit not in CNC_UNITS_IN_METRES:
        raise ValueError(f"Unknown base unit: '{base_unit}'")

    # Before the plain-number check: +5 must add to current, not be read as 5
    if current is not None and isinstance(value, str):
        result = _cnc_relative(value, base_unit, current)
        if result is not None:
            if not math.isfinite(result):
                raise ValueError(f"Expression does not give a finite number: '{value}'")
            return round(result, 10) if rounded else result

    try:
        result = cnc_float(value)
    except (ValueError, TypeError):
        result = None
    if result is not None:
        # float() reads "inf" and "1e999" as infinity. The letters of inf
        # can be typed into a field that takes units, so check here too.
        if not math.isfinite(result):
            raise ValueError(f"Not a finite number: '{value}'")
        return result

    if not isinstance(value, str):
        raise ValueError(f"Cannot evaluate {type(value).__name__} as a number")

    text = value.strip()
    if text.startswith('='):
        text = text[1:].strip()
    if not text or len(text) > _CNC_EXPRESSION_MAX_LENGTH:
        raise ValueError(f"Invalid number or expression: '{value}'")

    result, power = _cnc_evaluate(_cnc_tokens(text, value), value, base_unit)
    if not (_cnc_same(power, 0) or _cnc_same(power, 1)):
        raise ValueError(f"'{value}' is not a length")
    if not math.isfinite(result):
        raise ValueError(f"Expression does not give a finite number: '{value}'")
    # 1.4*25.4 is 35.559999999999995 in binary floating point. Rounding far
    # below any machine's resolution returns the 35.56 that was meant,
    # instead of storing the noise in a setting or the var file.
    return round(result, 10) if rounded else result


def normalizePath(path, base):
    if path is None or base is None:
        return
    path = os.path.expandvars(path)
    if path.startswith('~'):
        path = os.path.expanduser(path)
    elif not os.path.isabs(path):
        path = os.path.join(base, path)
    # if os.path.exists(path):
    return os.path.realpath(path)


def insertPath(env_var, index, file):
    files = os.getenv(env_var)
    if files is None:
        files =[]
    else:
        files.strip(':').split(':')
    print(files)
    files.insert(index, file)
    os.environ[env_var] = ':'.join(files)
    print((os.environ[env_var]))

import os
import locale


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

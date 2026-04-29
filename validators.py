import math

def to_float_safe(value) -> float | None:
    """
    Safely converts a value to float, handling Portuguese decimal commas,
    empty strings, None, and NaN.
    """
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        return value
    if isinstance(value, int):
        return float(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        value = value.replace(',', '.')
        try:
            res = float(value)
            if math.isnan(res):
                return None
            return res
        except ValueError:
            return None
    return None

def to_int_safe(value) -> int | None:
    """
    Safely converts a value to int, handling empty strings, None, and NaN.
    """
    float_val = to_float_safe(value)
    if float_val is None:
        return None
    try:
        return int(float_val)
    except ValueError:
        return None

def is_valid_price(value: float) -> bool:
    """
    Checks if a price value is valid (greater than or equal to 0).
    """
    if value is None or math.isnan(value):
        return False
    return value >= 0.0

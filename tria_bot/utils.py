from decimal import Context


def format_float_positional(x: float, precision: int = 8):
    """
    Convert the given float to a string,
    without resorting to scientific notation
    """
    ctx = Context()
    ctx.prec = precision
    d1 = ctx.create_decimal(repr(x))
    return format(d1, 'f')
import logging
from typing import Any, Type, TypeVar
from pydantic import TypeAdapter, BaseModel
from decimal import Context

KindType = TypeVar("KindType", bound=BaseModel)


def parse_object_as(kind: Type[KindType], data: Any, **kwargs) -> KindType:
    """Parse python object to pydantic model type

    Args:
        kind (Any): Pydantic model type
        data (Any): Python object

    Returns:
        Any: Pydantic model type instance
    """

    return TypeAdapter(kind).validate_python(data, **kwargs)


def format_float_positional(x: float, precision: int = 8):
    """
    Convert the given float to a string,
    without resorting to scientific notation
    """
    ctx = Context()
    ctx.prec = precision
    d1 = ctx.create_decimal(repr(x))
    return format(d1, "f")


def create_logger(name: str, level: int = logging.INFO, fmt=None):
    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # create file or console handler and set level
    handler = logging.StreamHandler()
    handler.setLevel(level)

    # create formatter
    fmt = fmt or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(fmt)

    # add formatter to ch
    handler.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(handler)

    return logger
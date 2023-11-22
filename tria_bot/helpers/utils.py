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

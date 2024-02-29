import inspect
import logging
from typing import Any, Callable, Iterable, Type, TypeVar
from pydantic import PydanticSchemaGenerationError, TypeAdapter, BaseModel

KindType = TypeVar("KindType", bound=BaseModel)

class NotSupportedType(Exception):
    ...


def parse_object_as(kind: Type[KindType], data: Any, **kwargs) -> KindType:
    """Parse python object to pydantic model type

    Args:
        kind (Any): Pydantic model type
        data (Any): Python object

    Returns:
        Any: Pydantic model type instance
    """

    try:
        return TypeAdapter(kind).validate_python(data, **kwargs)
    except PydanticSchemaGenerationError:
        raise NotSupportedType(f"Type {repr(kind)} is not supported")


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


async def async_filter(function: Callable, iterable: Iterable[Any]):
    async for item in iterable:
        should_yield = function(item)
        if inspect.isawaitable(should_yield):
            should_yield = await should_yield
        if should_yield:
            yield item

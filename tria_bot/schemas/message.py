from typing import Any, Dict, List, Union
from pydantic import BaseModel


class RedisMessage(BaseModel):
    # timestamp: int
    event: str
    data: Any


class ProffitMessage(RedisMessage):
    data: Dict[str, Any]

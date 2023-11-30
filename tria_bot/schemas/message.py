from typing import Any, Dict, List
from pydantic import BaseModel


class RedisMessage(BaseModel):
    # timestamp: int
    event: str
    data: Any


class ProffitMessage(RedisMessage):
    data: Dict[str, Any]

class GapsMessage(RedisMessage):
    data: List[Dict[str, Any]]


class TopVolumeMessage(RedisMessage):
    data: Dict[str, Any]
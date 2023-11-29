from typing import Tuple
from pydantic import BaseModel


class Proffit(BaseModel):
    alt: str
    strong: str
    stable: str
    value: float
    prices: Tuple[str, str, str]
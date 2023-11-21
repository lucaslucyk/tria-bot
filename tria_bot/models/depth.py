# models.py
from typing import List, Tuple
from aredis_om import Field
from tria_bot.models.base import JsonModelBase


class Depth(JsonModelBase):
    symbol: str = Field(index=True, alias="s", primary_key=True)
    bids: List[Tuple[str, str]] = Field(alias="b")
    asks: List[Tuple[str, str]] = Field(alias="a")
    event_time: int = Field(alias="E", index=True)

    class Meta:
        model_key_prefix = "Depth"
        global_key_prefix = "tria_bot"

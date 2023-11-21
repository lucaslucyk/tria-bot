# models.py
from aredis_om import Field
from tria_bot.models.base import JsonModelBase


class Ticker(JsonModelBase):
    symbol: str = Field(index=True, alias="s", primary_key=True)
    price_change: str = Field(alias="p")
    price_change_percent: str = Field(alias="P")
    event_time: int = Field(alias="E", index=True)

    class Meta:
        model_key_prefix = "Ticker"
        global_key_prefix = "tria_bot"

# models.py
from typing import List
from aredis_om import Field
from tria_bot.models.base import JsonModelBase
# from tria_bot.models.depth import Depth


class Proffit(JsonModelBase):
    assets: str = Field(index=True, alias="assets", primary_key=True)
    alt: str = Field(alias="alt", index=True)
    strong: str = Field(alias="strong", index=True)
    stable: str = Field(alias="stable", index=True)
    value: float = Field(alias="value")
    # depths: List[Depth] = Field(alias="depths")

    class Meta:
        model_key_prefix = "Proffit"
        global_key_prefix = "tria_bot"

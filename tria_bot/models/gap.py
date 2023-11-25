# models.py
from aredis_om import Field
from tria_bot.models.base import JsonModelBase


class Gap(JsonModelBase):
    assets: str = Field(index=True, alias="assets", primary_key=True)
    alt: str = Field(alias="alt", index=True)
    strong: str = Field(alias="strong", index=True)
    stable: str = Field(alias="stable", index=True)
    value: float = Field(alias="value")

    class Meta:
        model_key_prefix = "Gap"
        global_key_prefix = "tria_bot"

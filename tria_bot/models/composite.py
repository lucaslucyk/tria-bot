# models.py
from typing import List
from aredis_om import Field
from tria_bot.models.base import JsonModelBase


class TopAltAsset(JsonModelBase):
    index: int = Field(alias="index", index=True, primary_key=True)
    name: str = Field(index=True, alias="name")

    class Meta:
        model_key_prefix = "TopAltAsset"
        global_key_prefix = "tria_bot"


class TopAltAssets(JsonModelBase):
    assets: List[str] = Field(alias="assets")

    class Meta:
        PK_VALUE = "TOP_ALT_ASSETS"
        model_key_prefix = "TopAltAssets"
        global_key_prefix = "tria_bot"


class Symbol(JsonModelBase):
    symbol: str = Field(index=True, alias="symbol", primary_key=True)
    base_asset: str = Field(index=True, alias="baseAsset")
    quoteAsset: str = Field(index=True, alias="quoteAsset")
    is_spot_trading_allowed: bool = Field(
        index=True, alias="isSpotTradingAllowed"
    )
    max_qty: float = Field(alias="maxQty")
    min_qty: float = Field(alias="minQty")
    order_types: List[str] = Field(alias="orderTypes")
    permissions: List[str] = Field(alias="permissions")
    status: str = Field(index=True, alias="status")
    step_size: float = Field(alias="stepSize")
    tick_size: float = Field(alias="tickSize")

    class Meta:
        model_key_prefix = "Symbol"
        global_key_prefix = "tria_bot"

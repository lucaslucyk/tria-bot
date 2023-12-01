# models.py
from decimal import Decimal
from typing import List, Literal, Union
from aredis_om import Field
from tria_bot.models.base import JsonModelBase
from binance.helpers import round_step_size


class TopVolumeAsset(JsonModelBase):
    index: int = Field(alias="index", index=True, primary_key=True)
    name: str = Field(index=True, alias="name")

    class Meta:
        model_key_prefix = "TopVolumeAsset"
        global_key_prefix = "tria_bot"


class TopVolumeAssets(JsonModelBase):
    assets: List[str] = Field(alias="assets")

    class Meta:
        PK_VALUE = "TOP_VOLUME_ASSETS"
        model_key_prefix = "TopVolumeAssets"
        global_key_prefix = "tria_bot"


class ValidSymbols(JsonModelBase):
    symbols: List[str] = Field(alias="symbols")

    class Meta:
        PK_VALUE = "VALID_SYMBOLS"
        model_key_prefix = "ValidSymbols"
        global_key_prefix = "tria_bot"


class Symbol(JsonModelBase):
    symbol: str = Field(index=True, alias="symbol", primary_key=True)
    base_asset: str = Field(index=True, alias="baseAsset")
    quote_asset: str = Field(index=True, alias="quoteAsset")
    is_spot_trading_allowed: bool = Field(
        index=True, alias="isSpotTradingAllowed"
    )
    min_price: float = Field(alias="minPrice")
    max_price: float = Field(alias="maxPrice")
    tick_size: float = Field(alias="tickSize")
    min_qty: float = Field(alias="minQty")
    max_qty: float = Field(alias="maxQty")
    step_size: float = Field(alias="stepSize")
    order_types: List[str] = Field(alias="orderTypes")
    permissions: List[str] = Field(alias="permissions")
    status: str = Field(index=True, alias="status")

    class Meta:
        model_key_prefix = "Symbol"
        global_key_prefix = "tria_bot"

    def apply_step_size(self, value: Union[float, Decimal, str]) -> float:
        return round_step_size(quantity=value, step_size=float(self.step_size))

    def apply_tick_size(self, value: Union[float, Decimal, str]) -> float:
        return round_step_size(quantity=value, step_size=float(self.tick_size))

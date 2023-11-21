from typing import Any, Dict, List, Union
from aiohttp import ClientSession
from aiohttp.typedefs import StrOrURL
from yarl import URL


class AsyncClient(ClientSession):
    STABLE_ASSETS = (
        "USDT",
        "DAI",
        "BUSD",
        "TUSD",
        "USDC",
        "UST",
        "DGX",
        "PAX",
        "USDN",
        "TRIBE",
    )
    STRONG_ASSETS = (
        "BTC",
        "ETH",
        "BNB",
    )

    def __init__(self, version: str = "v1", **kwargs):
        headers = kwargs.pop("headers", {"Accept": "application/json"})
        base_url = kwargs.pop("base_url", "https://www.binance.com")
        super().__init__(base_url=base_url, headers=headers, **kwargs)

    @property
    def _base_path(self) -> str:
        return f"/bapi/composite/v1/public"

    def _build_url(self, str_or_url: StrOrURL) -> URL:
        if str_or_url.startswith("/"):
            str_or_url = self._base_path + str_or_url
        url = URL(str_or_url)

        if self._base_url is None:
            return url
        else:
            assert not url.is_absolute() and url.path.startswith("/")
            return self._base_url.join(url)

    @staticmethod
    def get_asset_name(asset: Union[str, dict]) -> str:
        return asset if isinstance(asset, str) else asset.get("name", "")

    def is_stable(self, asset: Union[str, dict]) -> bool:
        """Check if a asset is stable

        Args:
            asset (Union[str, dict]): Asset name or dict with `name` key.

        Returns:
            bool: True if is stable, False if not.
        """

        return self.get_asset_name(asset) in self.STABLE_ASSETS

    def is_strong(self, asset: Union[str, dict]) -> bool:
        """Check if a asset is strong

        Args:
            asset (Union[str, dict]): Asset name or dict with `name` key.

        Returns:
            bool: True if is strong, False if not.
        """
        return self.get_asset_name(asset) in self.STRONG_ASSETS

    def is_alt(self, asset: Union[str, dict]) -> bool:
        """Check if a asset is alt

        Args:
            asset (Union[str, dict]): Asset name or dict with `name` key.

        Returns:
            bool: True if is alt, False if not.
        """

        cn_ = self.get_asset_name(asset)
        return not self.is_stable(cn_) and not self.is_strong(cn_)

    async def marketing_symbol_list(self) -> Dict[str, Any]:
        async with self.get(url="/marketing/symbol/list") as response:
            return await response.json()

    def __volume_alt_symbols(self, symbol: Dict[str, Any]) -> bool:
        return all((bool(symbol.get("volume", None)), self.is_alt(symbol)))

    @staticmethod
    def __order_volume(symbol: Dict[str, Any]) -> bool:
        return symbol.get("volume", None)

    async def get_top_volume_assets(self, quantity: int = 10) -> List[str]:
        response = await self.marketing_symbol_list()
        market_symbols = response.get("data", [])
        data = sorted(
            filter(self.__volume_alt_symbols, market_symbols),
            key=self.__order_volume,
            reverse=True,
        )
        if len(data) < quantity:
            return data
        return list(s.get("name") for s in data[:quantity])

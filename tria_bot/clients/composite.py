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
    BASE_PATH = "/bapi/composite/v1/public"

    def __init__(self, **kwargs):
        headers = kwargs.pop("headers", {"Accept": "application/json"})
        base_url = kwargs.pop("base_url", "https://www.binance.com")
        super().__init__(base_url=base_url, headers=headers, **kwargs)

    async def __aenter__(self) -> "AsyncClient":
        return await super().__aenter__()

    def _build_url(self, str_or_url: StrOrURL) -> URL:
        if str_or_url.startswith("/"):
            str_or_url = self.BASE_PATH + str_or_url
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
        """Get json from /marketing/symbol/list

        Returns:
            Dict[str, Any]: Symbol list
        """
        async with self.get(url="/marketing/symbol/list") as response:
            return await response.json()

    def __volume_alt_filter(self, asset: Dict[str, Any]) -> bool:
        return all((bool(asset.get("volume", None)), self.is_alt(asset)))

    async def get_top_volume_assets(self, quantity: int = 10) -> List[str]:
        """Get top volume assets from Binance API

        Args:
            quantity (int, optional): Volume quantity. Defaults to 10.

        Returns:
            List[str]: Top volume assets
        """
        response = await self.marketing_symbol_list()
        market_assets = response.get("data", [])
        assets = sorted(
            filter(self.__volume_alt_filter, market_assets),
            key=lambda x: x["volume"],
            reverse=True,
        )
        if len(assets) < quantity:
            return assets
        return list(s.get("name") for s in assets[:quantity])

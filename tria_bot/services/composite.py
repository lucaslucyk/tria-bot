import asyncio
import os
from inspect import isawaitable
from typing import Any, Dict, Generator, Optional, Sequence, Tuple
from uuid import uuid1
import orjson
from pydantic import BaseModel
from aredis_om import get_redis_connection, Migrator, NotFoundError
from tria_bot.conf import settings
from tria_bot.crud.composite import (
    TopVolumeAssetsCRUD,
    SymbolsCRUD,
    ValidSymbolsCRUD,
)
from tria_bot.helpers.symbols import all_combos
from tria_bot.helpers.utils import async_filter, create_logger
from tria_bot.models.composite import TopVolumeAssets, Symbol, ValidSymbols
from tria_bot.clients.composite import AsyncClient
from tria_bot.clients.binance import AsyncClient as BinanceClient
from tria_bot.schemas.message import TopVolumeMessage


class SocketErrorDetail(BaseModel):
    code: int
    msg: str


class SocketError(Exception):
    ...


class CompositeSvc:
    loop_interval: float = settings.COMPOSITE_LOOP_INTERVAL
    model = TopVolumeAssets
    symbol_model = Symbol
    valid_symbols_model = ValidSymbols
    top_volume_change_event = "top-volume-change"

    def __init__(self, *args, **kwargs) -> None:
        self._uid = uuid1()
        self.logger = create_logger(f"{type(self).__name__}[{self._uid}]")
        self._redis_url = kwargs.get(
            "redis_om_url",
            os.environ.get("REDIS_OM_URL"),
        )
        self._redis_conn = None
        self._composite_client = None
        self._is_running: bool = True
        self._tva_crud = None
        self._valid_symbols_crud = None
        self._symbols_crud = None

        self._binance_symbols = None

    async def __aenter__(self) -> "CompositeSvc":
        await Migrator().run()
        self._redis_conn = get_redis_connection(url=self._redis_url)
        self._tva_crud = TopVolumeAssetsCRUD(conn=self._redis_conn)
        self._valid_symbols_crud = ValidSymbolsCRUD(conn=self._redis_conn)
        self._symbols_crud = SymbolsCRUD(conn=self._redis_conn)

        self._binance_symbols = await self.get_valid_symbols()

        return self

    async def __aexit__(
        self,
        exc_type: Optional[Any] = None,
        exc_val: Optional[Any] = None,
        exc_tb: Optional[Any] = None,
    ) -> None:
        await self._redis_conn.close()

    async def get_valid_symbols(self):
        async with BinanceClient() as client:
            return [s async for s in client.get_valid_symbols()]

    def _model_or_raise(self, data: Sequence[str]):
        return self.model(assets=data, pk=self.model.Meta.PK_VALUE)

    async def _db_or_empty(self) -> TopVolumeAssets:
        try:
            return await self._tva_crud.get(self.model.Meta.PK_VALUE)
        except NotFoundError:
            return self.model(assets=[""], pk=self.model.Meta.PK_VALUE)

    async def on_change_handler(
        self,
        old: Sequence[str],
        new: Sequence[str],
    ) -> None:
        """Top volume asset change event handler

        Args:
            old (Sequence[str]): Old top volume assets
            new (Sequence[str]): New top volume assets
        """

        msg = f"Top volume assets change from {old} to {new}"
        self.logger.info(msg)
        #data = {"event": self.top_volume_change_event, "old": old, "new": new}
        data = TopVolumeMessage(
            event=self.top_volume_change_event,
            data={
                "old": old,
                "new": new
            }
        )
        await self._redis_conn.publish(
            settings.PUBSUB_TOP_VOLUME_CHANNEL,
            orjson.dumps(data.model_dump()),
        )

    @staticmethod
    def map_filters(
        filters: Sequence[Dict[str, Any]]
    ) -> Generator[Tuple[str, Dict[str, Any]], Any, None]:
        """Map list of filters to dict with `filterType` key.

        Args:
            filters (Sequence[Dict[str, Any]]): List of symbol filters

        Yields:
            Iterator[Dict[str, Any]]: Map with `filterType` key and filter detail
        """
        for f in filters:
            yield f.get("filterType"), f

    def get_symbol_models(
        self,
        symbols: Sequence[Dict[str, Any]],
    ) -> Generator[Symbol, Any, None]:
        """Build Symbol models from Binance API response

        Args:
            symbols (Sequence[Dict[str, Any]]): Sequence of Binance symbol dict

        Yields:
            Generator[Symbol, Any, None]: Symbol model instance
        """
        for s in symbols:
            filters_map = dict(self.map_filters(s.get("filters", [])))
            yield Symbol(
                symbol=s.get("symbol", ""),
                status=s.get("status", ""),
                base_asset=s.get("baseAsset", ""),
                quote_asset=s.get("quoteAsset", ""),
                is_spot_trading_allowed=s.get("isSpotTradingAllowed", False),
                min_price=float(
                    filters_map.get("PRICE_FILTER", {}).get("minPrice", "0.0")
                ),
                max_price=float(
                    filters_map.get("PRICE_FILTER", {}).get("maxPrice", "0.0")
                ),
                tick_size=float(
                    filters_map.get("PRICE_FILTER", {}).get("tickSize", "0.0")
                ),
                min_qty=float(
                    filters_map.get("LOT_SIZE", {}).get("minQty", "0.0")
                ),
                max_qty=float(
                    filters_map.get("LOT_SIZE", {}).get("maxQty", "0.0")
                ),
                step_size=float(
                    filters_map.get("LOT_SIZE", {}).get("stepSize", "0.0")
                ),
                order_types=s.get("orderTypes", [""]),
                permissions=s.get("permissions", [""]),
            )

    async def _save_valid_symbols(self, symbols: Sequence[str]):
        self.logger.info("Refreshing valid symbols...")
        obj = self.valid_symbols_model(
            pk=self.valid_symbols_model.Meta.PK_VALUE,
            symbols=symbols,
        )
        return await self._valid_symbols_crud.save(obj)

    async def _save_symbols_info(self, symbols: Sequence[Dict[str, Any]]):
        self.logger.info("Refreshing symbols info...")
        symbol_models = self.get_symbol_models(symbols)
        return await self._symbols_crud.add(list(symbol_models))

    async def refresh_symbols(self, assets: Sequence[str]) -> None:
        """Get binance symbols and store data in database

        Args:
            assets (Sequence[str]): Current top volume assets
        """
        async with BinanceClient() as client:
            combos = all_combos(
                alt_assets=assets,
                stable_assets=(settings.USE_STABLE_ASSET,),
            )
            valids = list(filter(lambda x: x in self._binance_symbols, combos))
            symbols_info = await client.get_symbols_info(symbols=valids)

            await self._save_valid_symbols(symbols=valids)
            await self._save_symbols_info(symbols=symbols_info)

    async def handler(self, data: Sequence[str]) -> None:
        """Handle Composite top volume assets response

        Args:
            data (Sequence[str]): Top volume assets
        """
        model_data = await self._db_or_empty()
        if set(model_data.assets) != set(data):
            old = model_data.assets.copy()
            # save data
            model_data.assets = data
            await self._tva_crud.save(model_data)

            await self.on_change_handler(old=old, new=data)
            await self.refresh_symbols(assets=data)

    async def refresh(self, interval: Optional[float] = None) -> None:
        """Get top volume assets and refresh into database if change

        Args:
            interval (Optional[float], optional):
                Loop invertal. Defaults to None.
        """
        async with AsyncClient() as composite:
            self.logger.info("Connected to Binance API to get Top Assets.")
            while self._is_running:
                data = await composite.get_top_volume_assets()
                await self.handler(data=data)
                await asyncio.sleep(interval or self.loop_interval)

    @classmethod
    async def start(cls, interval: float = None) -> None:
        """Create CompositeSvc instance and start refresh loop

        Args:
            interval (float, optional): Loop interval. Defaults to None.
        """
        async with cls() as svc:
            await svc.refresh(interval=interval)

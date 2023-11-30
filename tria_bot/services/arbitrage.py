import asyncio
import os
from typing import Any, AsyncGenerator, Dict, Optional, Tuple
import anyio

import orjson
from tria_bot.clients.binance import AsyncClient, BinanceAPIException
from tria_bot.crud.composite import (
    SymbolsCRUD,
    TopVolumeAssetsCRUD as TVACrud,
    ValidSymbolsCRUD,
)
from tria_bot.crud.depths import DepthsCRUD
from tria_bot.models.composite import Symbol, TopVolumeAssets

# from tria_bot.models.proffit import Proffit
from tria_bot.schemas.proffit import Proffit
from tria_bot.schemas.message import ProffitMessage
from tria_bot.services.base import BaseSvc
from tria_bot.conf import settings


class TopVolumeChangeError(Exception):
    ...


class ArbitrageSvc(BaseSvc):
    proffit_channel = settings.PUBSUB_PROFFIT_CHANNEL
    top_volume_channel = settings.PUBSUB_TOP_VOLUME_CHANNEL

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__api_key = os.environ.get("BINANCE_API_KEY")
        self.__api_secret = os.environ.get("BINANCE_API_SECRET")
        self._binance = None
        # helpers
        self._tva_crud = None
        self._valid_symbols_crud = None
        self._symbols_info_crud = None
        self._depths_crud = None
        self._tva = None
        self._valid_symbols = None

        self._binance_helper = None

    async def __aenter__(self) -> "ArbitrageSvc":
        await super().__aenter__()

        # helpers
        self._tva_crud = TVACrud(conn=self._redis_conn)
        self._valid_symbols_crud = ValidSymbolsCRUD(conn=self._redis_conn)
        self._symbols_info_crud = SymbolsCRUD(conn=self._redis_conn)
        self._depths_crud = DepthsCRUD(conn=self._redis_conn)
        self._tva = await self._get_top_volume_assets()
        self._valid_symbols = await self._get_valid_symbols()
        self._symbols_info = [s async for s in self._get_symbols_info()]
        self._binance = await AsyncClient(
            api_key=self.__api_key,
            api_secret=self.__api_secret,
            symbols=self._symbols_info,
        ).__aenter__()
        self._binance_helper = self._binance._helper
        return self

    async def __aexit__(
        self,
        exc_type: Any | None = None,
        exc_val: Any | None = None,
        exc_tb: Any | None = None,
    ) -> None:
        if self._binance != None:
            await self._binance.__aexit__(exc_type, exc_val, exc_tb)
        return await super().__aexit__(exc_type, exc_val, exc_tb)

    async def _get_top_volume_assets(self) -> TopVolumeAssets:
        return await self._tva_crud.wait_for(self._tva_crud.model.Meta.PK_VALUE)

    async def _get_valid_symbols(self):
        return await self._valid_symbols_crud.wait_for(
            self._valid_symbols_crud.model.Meta.PK_VALUE
        )

    async def _get_symbols_info(
        self,
    ) -> AsyncGenerator[Tuple[str, Symbol], None]:
        for pk in self._valid_symbols.symbols:
            # symbol = await self._symbols_info_crud.get(pk)
            # yield symbol.symbol, symbol
            yield await self._symbols_info_crud.get(pk)

    async def get_proffit(self) -> ProffitMessage:
        proffit = None
        async with self._redis_conn.pubsub(
            ignore_subscribe_messages=True
        ) as ps:
            await ps.subscribe(self.proffit_channel, self.top_volume_channel)
            self.logger.info(f"Subscribed to {self.proffit_channel}")

            async for msg in ps.listen():
                if msg != None:
                    if msg["channel"] == self.top_volume_channel:
                        await ps.unsubscribe()
                        raise TopVolumeChangeError()

                    proffit = ProffitMessage(
                        **orjson.loads(msg["data"].encode())
                    )
                    await ps.unsubscribe()
                    break
                # await asyncio.sleep(.001)

        return proffit

    async def safe_cancel_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        try:
            orderId = order.get("orderId")
            self.logger.info(f"Canceling order {orderId}...")
            order = await self._binance.cancel_order(
                symbol=order.get("symbol"),
                orderId=orderId,
            )
            return await self._binance.wait_order_canceled(
                order=order,
                max_wait_time=settings.ORDER_MAX_WAIT_TIMES[0],
            )
        except BinanceAPIException as err:
            if err.code == -2011:
                # check order filled
                order = await self._binance.get_order(
                    orderId=orderId,
                    symbol=order.get("symbol"),
                )
                filled_status = (
                    self._binance.ORDER_STATUS_FILLED,
                    self._binance.ORDER_STATUS_PARTIALLY_FILLED,
                )
                if order.get("status", "").upper() in filled_status:
                    return order
                raise
            raise

    async def _buy_alt(self, proffit: Proffit) -> Dict[str, Any]:
        # 1. get free stable balance
        stable_free = await self._binance.wait_balance_released(proffit.stable)

        # 2. apply investment multiplier
        stable_use = round(stable_free * settings.INVESTMENT_MULTIPLIER, 8)

        msg = "Buying {asset} with {qty} {stable} at {price}...".format(
            asset=proffit.alt,
            qty=stable_use,
            stable=proffit.stable,
            price=proffit.prices[0],
        )
        self.logger.info(msg)

        # 3. apply step size
        order = await self._binance.limit_buy_asset(
            symbol=f"{proffit.alt}{proffit.stable}",
            price=float(proffit.prices[0]),
            ammount=stable_use,
        )

        # 4. wait order filled
        try:
            return await self._binance.wait_order_filled(
                order=order,
                max_wait_time=settings.ORDER_MAX_WAIT_TIMES[0],
            )
        except TimeoutError as err:
            self.logger.error(err)
            return await self.safe_cancel_order(order=order)
            # order = await self._binance.cancel_order(
            #     symbol=f"{proffit.alt}{proffit.stable}",
            #     orderId=order.get("orderId"),
            # )
            # return await self._binance.wait_order_canceled(
            #     order=order,
            #     max_wait_time=settings.ORDER_MAX_WAIT_TIMES[0],
            # )

    async def _sell_alt(
        self,
        proffit: Proffit,
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        available = await self._binance.wait_balance_released(proffit.alt)
        msg = "Selling {qty} {asset} at {price}...".format(
            qty=available, asset=proffit.alt, price=price or proffit.prices[1]
        )
        self.logger.info(msg)
        symbol = f"{proffit.alt}{proffit.strong}"

        # 3. apply step size
        order = await self._binance.limit_sell_asset(
            symbol=symbol,
            price=price or float(proffit.prices[1]),
            quantity=available,
        )

        # 4. wait order filled
        try:
            return await self._binance.wait_order_filled(
                order=order,
                max_wait_time=settings.ORDER_MAX_WAIT_TIMES[1],
            )
        except TimeoutError as err:
            self.logger.error(err)
            order = await self.safe_cancel_order(order=order)
            if not self._binance._is_order_canceled(order=order):
                return await self._binance.wait_order_filled(
                    order=order,
                    max_wait_time=settings.ORDER_MAX_WAIT_TIMES[2],
                )

            self.logger.info("Refreshing price...")
            depth = await self._depths_crud.get(symbol)
            return await self._sell_alt(proffit=proffit, price=depth.asks[0][0])

    async def _sell_strong(
        self,
        proffit: Proffit,
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        available = await self._binance.wait_balance_released(proffit.strong)
        symbol = f"{proffit.strong}{proffit.stable}"

        best_price = float(proffit.prices[2])
        if not price:
            depth = await self._depths_crud.get(symbol)
            best_price = max(float(depth.asks[0][0]), float(proffit.prices[2]))

        msg = "Selling {qty} {asset} at {price}...".format(
            qty=available, asset=proffit.strong, price=price or best_price
        )
        self.logger.info(msg)

        # 3. apply step size
        order = await self._binance.limit_sell_asset(
            symbol=f"{proffit.strong}{proffit.stable}",
            price=price or best_price,
            quantity=available,
        )

        # 4. wait order filled
        try:
            return await self._binance.wait_order_filled(
                order=order,
                max_wait_time=settings.ORDER_MAX_WAIT_TIMES[2],
            )
        except TimeoutError as err:
            self.logger.error(err)
            order = await self.safe_cancel_order(order=order)
            if not self._binance._is_order_canceled(order=order):
                return await self._binance.wait_order_filled(
                    order=order,
                    max_wait_time=settings.ORDER_MAX_WAIT_TIMES[2],
                )

            self.logger.info("Refreshing price...")
            depth = await self._depths_crud.get(symbol)
            return await self._sell_strong(
                proffit=proffit, price=depth.asks[0][0]
            )

    async def _calc_proffit(
        self, first_order: Dict[str, Any], last_order: Dict[str, float]
    ) -> Dict[str, Any]:
        real_invested = await self._binance.get_cummulative_quote_qty(
            order=first_order
        )
        real_obtained = await self._binance.get_cummulative_quote_qty(
            order=last_order
        )

        proffit_qty = round(real_obtained - real_invested, 8)
        proffit_percent = round(((real_obtained / real_invested) - 1) * 100, 2)
        return {"quantity": proffit_qty, "percent": proffit_percent}

    async def arbitrate(self, proffit: Proffit) -> None:
        self.logger.info(f"Arbitrating with {proffit}")

        # 1. buy alt asset
        alt_buy_order = await self._buy_alt(proffit=proffit)
        if self._binance._is_order_canceled(order=alt_buy_order):
            self.logger.info("Canceling arbitrage...")
            return

        # 2. selt alt asset
        alt_strong_order = await self._sell_alt(proffit=proffit)

        # 2. selt strong asset
        strong_stable_order = await self._sell_strong(proffit=proffit)

        self.logger.info("Arbitrage completed! Calculating proffit...")

        # calculate real proffit
        real_proffit = await self._calc_proffit(
            first_order=alt_buy_order,
            last_order=strong_stable_order,
        )
        msg = "Final proffit = {pp}% ({pq} {asset})".format(
            pp=real_proffit.get("percent", 0.0),
            pq=real_proffit.get("quantity", 0.0),
            asset=proffit.stable,
        )
        self.logger.info(msg)

    async def loop(self):
        try:
            proffit = await self.get_proffit()
            await self.arbitrate(proffit=Proffit(**proffit.data))
            await asyncio.sleep(0.01)
            return await self.loop()
        except TopVolumeChangeError:
            self.logger.info("Top volume has change. Stopping service...")
            pass

    @classmethod
    async def start(cls):
        while True:
            async with cls() as svc:
                await svc.loop()


if __name__ == "__main__":
    anyio.run(ArbitrageSvc.start)

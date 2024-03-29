from asyncio import sleep
import asyncio
import inspect
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
)
from binance import AsyncClient as BinanceAsyncClient
from binance.client import BaseClient
from binance.exceptions import BinanceAPIException
from time import time
from tria_bot.helpers.binance import Binance as BinanceHelper
from tria_bot.models.composite import Symbol


class SymbolInfoException(Exception):
    ...


class SymbolSizeException(Exception):
    ...


class Decorators:
    @staticmethod
    def retry_for_errors(*errors, max_retries: int = 3):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                for _ in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except BinanceAPIException as err:
                        if err.code not in errors:
                            raise
                    await asyncio.sleep(.5)
                raise Exception(f"Max retries ({max_retries}) reached.")

            return wrapper

        return decorator


# class SymbolsInfo:
#     def __init__(self, symbols: List[Symbol] = None) -> None:
#         if not symbols:
#             return
#         for symbol in symbols:
#             setattr(self, symbol.symbol, symbol)

#     def symbol_info(self, symbol: str) -> Symbol:
#         return getattr(self, symbol, None)


class AsyncClient(BinanceAsyncClient):
    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        requests_params: Dict[str, Any] | None = None,
        tld: str = "com",
        base_endpoint: str = BaseClient.BASE_ENDPOINT_DEFAULT,
        testnet: bool = False,
        loop=None,
        session_params: Dict[str, Any] | None = None,
        private_key: str | Path | None = None,
        private_key_pass: str | None = None,
        symbols: Optional[Sequence[Symbol]] = None,
    ):
        super().__init__(
            api_key,
            api_secret,
            requests_params,
            tld,
            base_endpoint,
            testnet,
            loop,
            session_params,
            private_key,
            private_key_pass,
        )
        # self._symbols = SymbolsInfo(symbols=symbols or [])
        self._helper = BinanceHelper(symbols=symbols)

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Any] = None,
        exc_val: Optional[Any] = None,
        exc_tb: Optional[Any] = None,
    ) -> None:
        await self.close_connection()

    @Decorators.retry_for_errors(-1021)
    async def _request_api(
        self,
        method,
        path,
        signed=False,
        version=BaseClient.PUBLIC_API_VERSION,
        **kwargs,
    ):
        return await super()._request_api(
            method, path, signed, version, **kwargs
        )

    async def get_valid_symbols(self) -> Generator[str, Any, None]:
        exchange_info = await self.get_exchange_info()
        for symbol in exchange_info.get("symbols", []):
            if all(
                (
                    symbol.get("status", None) == "TRADING",
                    "SPOT" in symbol.get("permissions", []),
                    "LIMIT" in symbol.get("orderTypes", []),
                )
            ):
                yield symbol.get("symbol", "")

    async def get_symbols_info(
        self,
        symbols: Iterable[str],
    ) -> List[Dict[str, Any]]:
        symbols = str(list(symbols)).replace("'", '"').replace(" ", "")
        response = await self._get(
            path="exchangeInfo",
            version=self.PRIVATE_API_VERSION,
            data={"symbols": symbols},
        )
        return response.get("symbols", [])

    # @Decorators.retry_for_errors(-2011)
    # async def cancel_order(self, **params):
    #     return await super().cancel_order(**params)

    async def get_assets_balance(
        self,
        assets: Iterable[str],
        **params,
        # ) -> filter[Dict[str, Any]]:
    ):
        def filter_assets(e: Dict[str, Any]) -> bool:
            return e.get("asset", "").upper() in assets

        res = await self.get_account(**params)
        return filter(filter_assets, res.get("balances", []))

    # def _get_size(self, symbol: str, kind: Literal["step", "tick"]) -> float:
    #     # check kind size
    #     kind_size: float = getattr(
    #         self._symbols.symbol_info(symbol=symbol), f"{kind}_size", None
    #     )

    #     if not kind_size:
    #         raise SymbolSizeException(f"Not {kind}Size for symbol {symbol}")

    #     # get step size (min quote)
    #     return float(kind_size)

    # def get_step_size(self, symbol: str) -> float:
    #     return self._get_size(symbol=symbol, kind="step")

    # def get_tick_size(self, symbol: str) -> float:
    #     return self._get_size(symbol=symbol, kind="tick")

    # def _apply_size(
    #     self,
    #     symbol: str,
    #     kind: Literal["step", "tick"],
    #     value: Union[float, Decimal, str],
    # ) -> float:
    #     kind_size = self._get_size(symbol=symbol, kind=kind)
    #     return round_step_size(quantity=value, step_size=kind_size)

    # def apply_step_size(
    #     self, symbol: str, value: Union[float, Decimal, str]
    # ) -> float:
    #     return self._apply_size(symbol=symbol, kind="step", value=value)

    # def apply_tick_size(
    #     self,
    #     symbol: str,
    #     value: Union[float, Decimal, str],
    # ) -> float:
    #     return self._apply_size(symbol=symbol, kind="tick", value=value)

    async def get_free_balance(self, asset: str, **params) -> float:
        balance = await self.get_asset_balance(asset=asset, **params)
        return float(balance.get("free", "0.0"))

    async def get_free_balances(
        self,
        assets: Iterable[str],
        **params,
    ) -> AsyncGenerator[Tuple[str, float], None]:
        for balance in await self.get_assets_balance(assets, **params):
            yield balance.get("asset", ""), float(balance.get("free", "0.0"))

    async def wait_balance_released(
        self,
        asset,
        retry_time: float = 1.0,
        **params,
    ) -> float:
        balance = await self.get_asset_balance(asset=asset, **params)
        locked = float(balance.get("locked", "0.0"))

        if locked > 0.0:
            await sleep(retry_time)
            return self.wait_balance_released(
                asset=asset,
                retry_time=retry_time,
                **params,
            )
        return float(balance.get("free", "0.0"))

    def _is_order_canceled(self, order: Dict[str, Any]) -> bool:
        return order.get("status", "").upper() in (
            self.ORDER_STATUS_CANCELED,
            self.ORDER_STATUS_PENDING_CANCEL,
        )

    def _is_order_filled(self, order: Dict[str, Any]) -> bool:
        return order.get("status", "") == self.ORDER_STATUS_FILLED

    async def wait_order_condition(
        self,
        order: Dict[str, Any],
        conditions: Sequence[Callable],
        max_wait_time: float,
        retry_time: float = 1.0,
        start_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        start_time = start_time or time()
        if time() - start_time >= max_wait_time:
            raise TimeoutError(f"Max wait time ({max_wait_time}) reached.")

        order_id = order.get("orderId")
        symbol = order.get("symbol")

        for condition in conditions:
            result = condition(order)
            if inspect.isawaitable(result):
                result = await result
            if bool(result):
                return order

        await sleep(retry_time)
        updated_order = await self.get_order(symbol=symbol, orderId=order_id)
        return await self.wait_order_condition(
            order=updated_order,
            conditions=conditions,
            max_wait_time=max_wait_time,
            retry_time=retry_time,
            start_time=start_time,
        )

    async def wait_order_filled(
        self,
        order: Dict[str, Any],
        max_wait_time: float,
        retry_time: float = 1.0,
    ) -> Dict[str, Any]:
        return await self.wait_order_condition(
            order=order,
            conditions=[self._is_order_filled, self._is_order_canceled],
            max_wait_time=max_wait_time,
            retry_time=retry_time,
        )

    async def wait_order_canceled(
        self,
        order: Dict[str, Any],
        max_wait_time: float,
        retry_time: float = 1.0,
    ) -> Dict[str, Any]:
        return await self.wait_order_condition(
            order=order,
            conditions=[self._is_order_canceled],
            max_wait_time=max_wait_time,
            retry_time=retry_time,
        )

    async def limit_buy_asset(
        self,
        symbol: str,
        price: float,
        quantity: Optional[float] = None,
        ammount: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not quantity and not ammount:
            raise ValueError("Must specify quantity or ammount")
        if quantity and ammount:
            raise ValueError("Must specify only one quantity or ammount")

        to_buy = self._helper.apply_step_size(
            symbol=symbol,
            value=quantity or (ammount / price),
        )
        to_buy = self._helper._ffp(x=to_buy)

        exchange_price = self._helper.apply_tick_size(
            symbol=symbol, value=price
        )
        exchange_price = self._helper._ffp(x=exchange_price)
        return await self.order_limit_buy(
            symbol=symbol,
            quantity=to_buy,
            price=exchange_price,
        )

    async def limit_sell_asset(
        self,
        symbol: str,
        price: float,
        quantity: Optional[float] = None,
    ) -> Dict[str, Any]:
        to_sell = self._helper.apply_step_size(symbol=symbol, value=quantity)
        to_sell = self._helper._ffp(x=to_sell)
        exchange_price = self._helper.apply_tick_size(
            symbol=symbol, value=price
        )
        exchange_price = self._helper._ffp(x=exchange_price)

        return await self.order_limit_sell(
            symbol=symbol,
            quantity=to_sell,
            price=exchange_price,
        )

    async def get_cummulative_quote_qty(self, order: Dict[str, Any]) -> float:
        cqq = order.get("cummulativeQuoteQty", None)
        if not cqq:
            order = await self.get_order(
                orderId=order.get("orderId", ""),
                symbol=order.get("symbol", ""),
            )
            return await self.get_cummulative_quote_qty(order=order)

        return float(cqq)

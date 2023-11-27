from decimal import Decimal
from typing import AsyncGenerator, Literal, Tuple, Union
from binance.helpers import round_step_size
import orjson
from tria_bot.clients.binance import AsyncClient
from tria_bot.conf import settings
from tria_bot.crud.depths import DepthsCRUD
from tria_bot.helpers.symbols import all_combos, STRONG_ASSETS
from tria_bot.models.composite import Symbol, TopVolumeAssets, ValidSymbols
from tria_bot.models.depth import Depth
from tria_bot.models.gap import Gap
from tria_bot.models.proffit import Proffit
from tria_bot.models.ticker import Ticker
from tria_bot.services.base import BaseSvc
from tria_bot.crud.composite import (
    SymbolsCRUD,
    TopVolumeAssetsCRUD as TVACrud,
    ValidSymbolsCRUD,
)
from tria_bot.crud.tickers import TickersCRUD
from tria_bot.crud.proffits import ProffitsCRUD
from aredis_om import NotFoundError, Migrator


class ProffitSvc(BaseSvc):
    tva_model = TopVolumeAssets
    tickers_model = Ticker
    depths_model = Depth
    proffit_model = Proffit
    gap_model = Gap
    symbol_model = Symbol
    valid_symbols_model = ValidSymbols
    stable = settings.USE_STABLE_ASSET
    binance_fee = settings.BINANCE_FEE_MULTIPLIER
    min_proffit_detect = settings.MIN_PROFFIT_DETECT
    proffit_event = "proffit-detected"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tva_crud = None
        self._tva = None
        self._tickers_crud = None
        self._depths_crud = None
        self._proffits_crud = None
        self._valid_symbols_crud = None
        self._symbols_info_crud = None
        self._valid_symbols = None
        self._symbols_info = None

        self._is_running = True

    async def _get_top_volume_assets(self) -> TopVolumeAssets:
        return await self._tva_crud.wait_for(self.tva_model.Meta.PK_VALUE)

    async def _get_symbols_info(
        self,
    ) -> AsyncGenerator[Tuple[str, Symbol], None]:
        for pk in self._valid_symbols.symbols:
            symbol = await self._symbols_info_crud.get(pk)
            yield symbol.symbol, symbol

    async def _get_valid_symbols(self):
        return await self._valid_symbols_crud.wait_for(
            self.valid_symbols_model.Meta.PK_VALUE
        )

    async def _get_all_symbols(self):
        return list(
            all_combos(
                alt_assets=self._tva.assets,
                stable_assets=(self.stable,),
            )
        )

    async def __aenter__(self) -> "ProffitSvc":
        await super().__aenter__()
        await Migrator().run()
        self._tva_crud = TVACrud(conn=self._redis_conn)
        self._valid_symbols_crud = ValidSymbolsCRUD(conn=self._redis_conn)
        self._tickers_crud = TickersCRUD(conn=self._redis_conn)
        self._depths_crud = DepthsCRUD(conn=self._redis_conn)
        self._proffits_crud = ProffitsCRUD(conn=self._redis_conn)
        self._symbols_info_crud = SymbolsCRUD(conn=self._redis_conn)
        self._tva = await self._get_top_volume_assets()
        self._valid_symbols = await self._get_valid_symbols()
        self._symbols_info = {k: v async for k, v in self._get_symbols_info()}
        await self.wait_depth()
        return self

    async def wait_depth(self) -> None:
        self.logger.info("Waiting for a symbol depth...")
        await self._depths_crud.wait_for(self._valid_symbols.symbols[0])
        self.logger.info("Done!")

    def _get_size(self, symbol: str, kind: Literal["step", "tick"]) -> float:
        info = self._symbols_info.get(symbol, None)
        if not info:
            raise KeyError(f"Symbol {symbol} not found")
        kind_size = getattr(info, f"{kind}_size", None)
        if kind_size == None:
            raise ValueError(f"Not {kind} size for symbol {symbol}")
        return float(kind_size)

    def get_step_size(self, symbol: str) -> float:
        return self._get_size(symbol=symbol, kind="step")

    def get_tick_size(self, symbol: str) -> float:
        return self._get_size(symbol=symbol, kind="tick")

    def _apply_size(
        self,
        symbol: str,
        kind: Literal["step", "tick"],
        value: Union[float, Decimal, str],
    ) -> float:
        kind_size = self._get_size(symbol=symbol, kind=kind)
        return round_step_size(quantity=value, step_size=kind_size)

    def apply_step_size(
        self, symbol: str, value: Union[float, Decimal, str]
    ) -> float:
        return self._apply_size(symbol=symbol, kind="step", value=value)

    def apply_tick_size(
        self,
        symbol: str,
        value: Union[float, Decimal, str],
    ) -> float:
        return self._apply_size(symbol=symbol, kind="tick", value=value)

    def calc_proffit(
        self,
        alt_stable_depth: Depth,
        alt_strong_depth: Depth,
        strong_stable_depth: Depth,
        ammount: float = 100.0,
        percent: bool = True,
    ):
        alt_stable_price = float(alt_stable_depth.bids[0][0])
        alt_qty = (ammount / alt_stable_price) * self.binance_fee
        alt_sell_qty = self.apply_step_size(
            symbol=alt_strong_depth.symbol,
            value=alt_qty,
        )

        alt_strong_price = float(alt_strong_depth.asks[0][0])
        strong_qty = alt_sell_qty * alt_strong_price * self.binance_fee

        strong_sell_qty = self.apply_step_size(
            symbol=strong_stable_depth.symbol, value=strong_qty
        )
        strong_stable_price = float(strong_stable_depth.asks[0][0])
        stable_qty = strong_sell_qty * strong_stable_price * self.binance_fee

        proffit = stable_qty / ammount - 1
        if percent:
            proffit = proffit * 100
        return round(proffit, 2)

    def _is_valid_symbol(self, symbol: str) -> bool:
        return symbol in self._valid_symbols.symbols

    async def publish_proffit(self, proffit: Proffit) -> None:
        data = {"event": self.proffit_event, "proffit": proffit.json()}
        await self._redis_conn.publish(
            settings.PUBSUB_PROFFIT_CHANNEL,
            orjson.dumps(data),
        )

    async def calc_proffits(self):
        # TODO: do this parallel
        for stg in STRONG_ASSETS:
            strong_stable_symbol = f"{stg}{self.stable}"
            if not self._is_valid_symbol(strong_stable_symbol):
                continue

            strong_stable = await self._depths_crud.get(strong_stable_symbol)

            for alt in self._tva.assets:
                alt_strong_symbol = f"{alt}{stg}"
                alt_stable_symbol = f"{alt}{self.stable}"
                if not all(
                    (
                        self._is_valid_symbol(alt_strong_symbol),
                        self._is_valid_symbol(alt_stable_symbol),
                    )
                ):
                    continue

                alt_stable = await self._depths_crud.get(alt_stable_symbol)
                alt_strong = await self._depths_crud.get(alt_strong_symbol)

                proffit = self.calc_proffit(
                    alt_stable_depth=alt_stable,
                    alt_strong_depth=alt_strong,
                    strong_stable_depth=strong_stable,
                    ammount=100,
                    percent=True,
                )
                if proffit > self.min_proffit_detect:
                    yield self.proffit_model(
                        assets=f"{alt}-{stg}-{self.stable}",
                        alt=alt,
                        strong=stg,
                        stable=self.stable,
                        value=proffit,
                    )

    async def proffit_loop(self):
        while self._is_running:
            # proffits = [p async for p in self.calc_proffits()]
            async for proffit in self.calc_proffits():
                self.logger.info(f"New proffit detectec ({proffit})")
                await self.publish_proffit(proffit=proffit)
            #await self._proffits_crud.add(proffits)

    @classmethod
    async def start(cls) -> None:
        async with cls() as svc:
            await svc.proffit_loop()

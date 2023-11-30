from ast import List
import asyncio
import time
from typing import AsyncGenerator, Iterable, Sequence, Tuple
from binance.helpers import round_step_size
import orjson
from tria_bot.conf import settings
from tria_bot.crud.depths import DepthsCRUD
from tria_bot.helpers.binance import Binance as BinanceHelper
from tria_bot.helpers.symbols import all_combos, STRONG_ASSETS
from tria_bot.models.composite import Symbol, TopVolumeAssets, ValidSymbols
from tria_bot.models.depth import Depth

# from tria_bot.models.gap import Gap
from tria_bot.schemas.gap import Gap

# from tria_bot.models.proffit import Proffit
from tria_bot.schemas.proffit import Proffit
from tria_bot.models.ticker import Ticker
from tria_bot.schemas.message import (
    GapsMessage,
    MultiProffitMessage,
    ProffitMessage,
)
from tria_bot.services.base import BaseSvc
from tria_bot.crud.composite import (
    SymbolsCRUD,
    TopVolumeAssetsCRUD as TVACrud,
    ValidSymbolsCRUD,
)
from tria_bot.crud.tickers import TickersCRUD
from tria_bot.crud.proffits import ProffitsCRUD
from aredis_om import NotFoundError, Migrator


class TopVolumeChangeError(Exception):
    ...


class ProffitSvc(BaseSvc):
    tva_model = TopVolumeAssets
    tickers_model = Ticker
    depths_model = Depth
    # proffit_model = Proffit
    proffit_model = Proffit
    # gap_model = Gap
    symbol_model = Symbol
    valid_symbols_model = ValidSymbols
    stable = settings.USE_STABLE_ASSET
    # TODO: get from api and use fee by symbol
    fee_mult = 1 - settings.EXCHANGE_FEE
    min_proffit_detect = settings.MIN_PROFFIT_DETECT
    proffit_event = "proffit-detected"
    calc_index = settings.PROFFIT_INDEX
    proffit_percent_format = settings.PROFFIT_PERCENT_FORMAT
    top_volume_channel = settings.PUBSUB_TOP_VOLUME_CHANNEL
    gaps_channel = settings.PUBSUB_GAPS_CHANNEL

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
        self._binance_helper = None
        self._is_running = True

    async def _get_top_volume_assets(self) -> TopVolumeAssets:
        return await self._tva_crud.wait_for(self.tva_model.Meta.PK_VALUE)

    async def _get_symbols_info(
        self,
    ) -> AsyncGenerator[Tuple[str, Symbol], None]:
        for pk in self._valid_symbols.symbols:
            # symbol = await self._symbols_info_crud.get(pk)
            # yield symbol.symbol, symbol
            yield await self._symbols_info_crud.get(pk)

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
        # self._symbols_info = {k: v async for k, v in self._get_symbols_info()}
        self._symbols_info = [s async for s in self._get_symbols_info()]
        self._binance_helper = BinanceHelper(symbols=self._symbols_info)
        await self.wait_depth()
        return self

    async def wait_depth(self) -> None:
        self.logger.info("Waiting for last symbol depth...")
        await self._depths_crud.wait_for(self._valid_symbols.symbols[-1])
        self.logger.info("Done!")

    async def ps_subscribe(self):
        async with self._redis_conn.pubsub(
            ignore_subscribe_messages=True
        ) as ps:
            await ps.subscribe(self.top_volume_channel)
            self.logger.info(f"Subscribed to {self.top_volume_channel}")
            async for msg in ps.listen():
                if msg != None:
                    self.logger.info("Top Volume Assets has changed")
                    self._is_running = False
                    await ps.unsubscribe()
                    break

    def calc_proffit(
        self,
        alt_stable_depth: Depth,
        alt_strong_depth: Depth,
        strong_stable_depth: Depth,
        ammount: float = 100.0,
        # percent: bool = True,
    ):
        alt_stable_price = float(alt_stable_depth.bids[self.calc_index][0])
        alt_qty = (ammount / alt_stable_price) * self.fee_mult
        # alt_sell_qty = self.apply_step_size(
        alt_sell_qty = self._binance_helper.apply_step_size(
            symbol=alt_strong_depth.symbol,
            value=alt_qty,
        )

        alt_strong_price = float(alt_strong_depth.asks[self.calc_index][0])
        strong_qty = alt_sell_qty * alt_strong_price * self.fee_mult

        # strong_sell_qty = self.apply_step_size(
        strong_sell_qty = self._binance_helper.apply_step_size(
            symbol=strong_stable_depth.symbol,
            value=strong_qty,
        )
        strong_stable_price = float(
            strong_stable_depth.asks[self.calc_index][0]
        )
        stable_qty = strong_sell_qty * strong_stable_price * self.fee_mult

        proffit = stable_qty / ammount - 1
        if self.proffit_percent_format:
            proffit = proffit * 100
        return round(proffit, 2)

    def _is_valid_symbol(self, symbol: str) -> bool:
        return symbol in self._valid_symbols.symbols

    async def get_gaps(self) -> GapsMessage:
        gaps = None
        async with self._redis_conn.pubsub(
            ignore_subscribe_messages=True
        ) as ps:
            await ps.subscribe(self.gaps_channel, self.top_volume_channel)
            self.logger.info(f"Subscribed to {self.gaps_channel}")

            async for msg in ps.listen():
                if msg != None:
                    if msg["channel"] == self.top_volume_channel:
                        await ps.unsubscribe()
                        raise TopVolumeChangeError()

                    gaps = GapsMessage(**orjson.loads(msg["data"].encode()))
                    await ps.unsubscribe()
                    break
                # await asyncio.sleep(.001)

        return gaps

    async def get_depths(self, *symbols):
        for symbol in symbols:
            yield await self._depths_crud.get(symbol)

    async def strict_calc_proffits(self, gaps: Iterable[Gap]):
        for gap in gaps:
            try:
                alt_stable_symbol = f"{gap.alt}{gap.stable}"
                alt_strong_symbol = f"{gap.alt}{gap.strong}"
                strong_stable_symbol = f"{gap.strong}{gap.stable}"

                depths = [
                    depth
                    async for depth in self.get_depths(
                        alt_stable_symbol,
                        alt_strong_symbol,
                        strong_stable_symbol,
                    )
                ]
                proffit = self.calc_proffit(
                    alt_stable_depth=depths[0],
                    alt_strong_depth=depths[1],
                    strong_stable_depth=depths[2],
                    ammount=100,
                )
                if proffit > self.min_proffit_detect:
                    yield self.proffit_model(
                        alt=gap.alt,
                        strong=gap.strong,
                        stable=gap.stable,
                        value=proffit,
                        prices=(
                            depths[0].bids[self.calc_index][0],
                            depths[1].asks[self.calc_index][0],
                            depths[2].asks[self.calc_index][0],
                        ),
                    )

            except NotFoundError:
                continue

    async def strict_loop(self):
        try:
            gaps = await self.get_gaps()
            self.logger.info("Gaps detected! Calculating proffits...")
            proffits = [
                proffit
                async for proffit in self.strict_calc_proffits(
                    gaps=(Gap(**g) for g in gaps.data)
                )
            ]
            if proffits:
                self.logger.info("Potential proffits detected!")
                await self.publish_proffits(proffits=proffits)
            await asyncio.sleep(0.01)
            return await self.strict_loop()
        except TopVolumeChangeError:
            self.logger.info("Top volume has change. Stopping service...")
            pass

    async def calc_proffits(self):
        # TODO: do this parallel
        for stg in STRONG_ASSETS:
            try:
                strong_stable_symbol = f"{stg}{self.stable}"
                if not self._is_valid_symbol(strong_stable_symbol):
                    continue
                strong_stable = await self._depths_crud.get(
                    strong_stable_symbol
                )
            except NotFoundError:
                continue

            for alt in self._tva.assets:
                try:
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
                        # percent=True,
                    )
                    if proffit > self.min_proffit_detect:
                        yield self.proffit_model(
                            # assets=f"{alt}-{stg}-{self.stable}",
                            alt=alt,
                            strong=stg,
                            stable=self.stable,
                            value=proffit,
                            prices=(
                                alt_stable.bids[self.calc_index][0],
                                alt_strong.asks[self.calc_index][0],
                                strong_stable.asks[self.calc_index][0],
                            ),
                        )
                except NotFoundError:
                    continue

    async def publish_proffits(self, proffits: Sequence[Proffit]):
        msg = MultiProffitMessage(
            event=self.proffit_event, data=[p.model_dump() for p in proffits]
        )
        await self._redis_conn.publish(
            settings.PUBSUB_MULTI_PROFFIT_CHANNEL,
            orjson.dumps(msg.model_dump()),
        )

    async def publish_proffit(self, proffit: Proffit) -> None:
        msg = ProffitMessage(
            # timestamp=int(time.time_ns() / 1000000),
            event=self.proffit_event,
            data=proffit.model_dump(),
        )
        # data = {"event": self.proffit_event, "data": proffit.dict()}
        await self._redis_conn.publish(
            settings.PUBSUB_PROFFIT_CHANNEL,
            # orjson.dumps(data),
            orjson.dumps(msg.model_dump()),
        )

    async def proffit_loop(self):
        while self._is_running:
            # proffits = [p async for p in self.calc_proffits()]
            async for proffit in self.calc_proffits():
                # self.logger.info(f"New proffit detectec ({proffit})")
                await self.publish_proffit(proffit=proffit)
            # await self._proffits_crud.add(proffits)

    @classmethod
    async def start(cls, strict: bool) -> None:
        while True:
            async with cls() as svc:
                if strict:
                    svc.logger.info("Starting service with strict mode...")
                    await svc.strict_loop()
                else:
                    svc.logger.info("Starting service...")
                    await asyncio.gather(svc.proffit_loop(), svc.ps_subscribe())

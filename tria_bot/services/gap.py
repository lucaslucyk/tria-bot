import asyncio
from typing import Sequence

import orjson
from tria_bot.conf import settings
from tria_bot.helpers.symbols import all_combos, STRONG_ASSETS
from tria_bot.helpers.utils import async_filter
from tria_bot.models.composite import TopVolumeAssets, ValidSymbols
# from tria_bot.models.gap import Gap
from tria_bot.schemas.gap import Gap
from tria_bot.models.ticker import Ticker
from tria_bot.services.base import BaseSvc
from tria_bot.crud.composite import (
    TopVolumeAssetsCRUD as TVACrud,
    ValidSymbolsCRUD as VSCrud,
)
from tria_bot.crud.tickers import TickersCRUD
from tria_bot.crud.gaps import GapsCRUD
from aredis_om import NotFoundError, Migrator


class GapCalculatorSvc(BaseSvc):
    tva_model = TopVolumeAssets
    tickers_model = Ticker
    gap_model = Gap
    valid_symbols_model = ValidSymbols
    stable = settings.USE_STABLE_ASSET
    top_volume_channel = settings.PUBSUB_TOP_VOLUME_CHANNEL
    gaps_channel = settings.PUBSUB_GAPS_CHANNEL
    gaps_event = "gaps-event"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tva_crud = None
        self._tva = None
        self._tickers_crud = None
        # self._gaps_crud = None
        self._valid_symbols_crud = None
        self._valid_symbols = None

        self._is_running = True


    async def __aenter__(self) -> "GapCalculatorSvc":
        await super().__aenter__()
        await Migrator().run()
        self._tva_crud = TVACrud(conn=self._redis_conn)
        self._tickers_crud = TickersCRUD(conn=self._redis_conn)
        # self._gaps_crud = GapsCRUD(conn=self._redis_conn)
        self._valid_symbols_crud = VSCrud(conn=self._redis_conn)
        self._tva = await self._get_top_volume_assets()
        self._valid_symbols = await self._get_valid_symbols()

        return self

    async def _get_top_volume_assets(self):
        return await self._tva_crud.wait_for(self.tva_model.Meta.PK_VALUE)

    async def _get_valid_symbols(self):
        return await self._valid_symbols_crud.wait_for(
            self.valid_symbols_model.Meta.PK_VALUE
        )

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

    async def calc_gaps(self):
        for alt in self._tva.assets:
            try:
                alt_stable_symbol = f"{alt}{self.stable}"
                if alt_stable_symbol not in self._valid_symbols.symbols:
                    continue

                stable = await self._tickers_crud.get(alt_stable_symbol)
                stable_pcp = float(stable.price_change_percent)

                for stg in STRONG_ASSETS:
                    alt_strong_symbol = f"{alt}{stg}"
                    if alt_stable_symbol not in self._valid_symbols.symbols:
                        continue
                    strong = await self._tickers_crud.get(alt_strong_symbol)
                    strong_pcp = float(strong.price_change_percent)
                    yield self.gap_model(
                        # assets=f"{alt}-{stg}-{self.stable}",
                        alt=alt,
                        strong=stg,
                        stable=self.stable,
                        value=round(strong_pcp - stable_pcp, 2),
                    )
            except NotFoundError:
                pass

    # async def calc_publish_gaps(self) -> None:
    #     data = {"event": self.gaps_event, "gaps": [
    #         gap.dict()
    #         async for gap in self.calc_gaps()
    #     ]}
        
    #     await self._redis_conn.publish(
    #         settings.PUBSUB_PROFFIT_CHANNEL,
    #         orjson.dumps(data),
    #     )

    async def publish_gaps(self, gaps: Sequence[Gap]) -> None:
        data = {"event": self.gaps_event, "data": [g.model_dump() for g in gaps]}
        await self._redis_conn.publish(
            settings.PUBSUB_GAPS_CHANNEL,
            orjson.dumps(data)
        )

    async def gaps_loop(self):
        while self._is_running:
            await self.calc_publish_gaps()

    async def gaps_loop(self):
        while self._is_running:

            def is_valid(gap: Gap) -> bool:
                return gap.value >= settings.GAP_MIN

            gaps = [_ async for _ in async_filter(is_valid, self.calc_gaps())]
            if gaps:
                # await self._gaps_crud.add(models=gaps)
                await self.publish_gaps(gaps=gaps)

    @classmethod
    async def start(cls):
        while True:
            async with cls() as svc:
                svc.logger.info("Starting service...")
                await asyncio.gather(svc.gaps_loop(), svc.ps_subscribe())

from tria_bot.conf import settings
from tria_bot.crud.gaps import GapsCRUD
from tria_bot.helpers.symbols import all_combos, STRONG_ASSETS
from tria_bot.models.composite import TopVolumeAssets
from tria_bot.models.gap import Gap
from tria_bot.models.ticker import Ticker
from tria_bot.services.base import BaseSvc
from tria_bot.crud.top_volume_assets import TopVolumeAssetsCRUD as TVACrud
from tria_bot.crud.tickers import TickersCRUD
from aredis_om import NotFoundError, Migrator


class GapCalculatorSvc(BaseSvc):
    tva_model = TopVolumeAssets
    tickers_model = Ticker
    gap_model = Gap
    stable = settings.USE_STABLE_ASSET

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tva_crud = None
        self._tva = None
        self._tickers_crud = None
        self._gaps_crud = None

    async def _get_top_volume_assets(self):
        return await self._tva_crud.wait_for(self.tva_model.Meta.PK_VALUE)

    async def _get_all_symbols(self):
        return list(
            all_combos(
                alt_assets=self._tva.assets,
                stable_assets=(self.stable,),
            )
        )

    async def __aenter__(self) -> "GapCalculatorSvc":
        await super().__aenter__()
        await Migrator().run()
        self._tva_crud = TVACrud(conn=self._redis_conn)
        self._tickers_crud = TickersCRUD(conn=self._redis_conn)
        self._gaps_crud = GapsCRUD(conn=self._redis_conn)
        self._tva = await self._get_top_volume_assets()
        self._symbols = await self._get_all_symbols()

        return self

    async def calc_gaps(self):
        for alt in self._tva.assets:
            try:
                stable = await self._tickers_crud.get(f"{alt}{self.stable}")
                stable_pcp = float(stable.price_change_percent)

                for stg in STRONG_ASSETS:
                    strong = await self._tickers_crud.get(f"{alt}{stg}")
                    strong_pcp = float(strong.price_change_percent)
                    yield self.gap_model(
                        assets=f"{alt}-{stg}-{self.stable}",
                        alt=alt,
                        strong=stg,
                        stable=self.stable,
                        value=round(strong_pcp - stable_pcp, 2)
                    )
            except NotFoundError:
                pass

    async def start(self):
        while True:
            # async for gap in self.calc_gaps():
            #     if gap.value > 1.0:
            #         self.logger.info(gap)
            gaps = [gap async for gap in self.calc_gaps()]
            await self._gaps_crud.add(models=gaps)

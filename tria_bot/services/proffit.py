from tria_bot.clients.binance import AsyncClient
from tria_bot.conf import settings
from tria_bot.crud.depths import DepthsCRUD
from tria_bot.helpers.symbols import all_combos, STRONG_ASSETS
from tria_bot.models.composite import TopVolumeAssets, ValidSymbols
from tria_bot.models.depth import Depth
from tria_bot.models.gap import Gap
from tria_bot.models.proffit import Proffit
from tria_bot.models.ticker import Ticker
from tria_bot.services.base import BaseSvc
from tria_bot.crud.composite import (
    TopVolumeAssetsCRUD as TVACrud,
    ValidSymbolsCRUD,
)
from tria_bot.crud.tickers import TickersCRUD
from tria_bot.crud.proffits import ProffitsCRUD
from aredis_om import NotFoundError, Migrator


class GapCalculatorSvc(BaseSvc):
    tva_model = TopVolumeAssets
    tickers_model = Ticker
    depths_model = Depth
    proffit_model = Proffit
    gap_model = Gap
    valid_symbols_model = ValidSymbols
    stable = settings.USE_STABLE_ASSET

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tva_crud = None
        self._tva = None
        self._tickers_crud = None
        self._depths_crud = None
        self._proffits_crud = None
        self._valid_symbols_crud = None
        self._valid_symbols = None
        self._symbols_info = None

    async def _get_top_volume_assets(self):
        return await self._tva_crud.wait_for(self.tva_model.Meta.PK_VALUE)

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

    async def _get_symbols_info(self):
        async with AsyncClient() as client:
            return await client.get_symbols_info(
                symbols=self._valid_symbols.symbols
            )

    async def __aenter__(self) -> "GapCalculatorSvc":
        await super().__aenter__()
        await Migrator().run()
        self._tva_crud = TVACrud(conn=self._redis_conn)
        self._valid_symbols_crud = ValidSymbolsCRUD(conn=self._redis_conn)
        self._tickers_crud = TickersCRUD(conn=self._redis_conn)
        self._depths_crud = DepthsCRUD(conn=self._redis_conn)
        self._proffits_crud = ProffitsCRUD(conn=self._redis_conn)
        self._tva = await self._get_top_volume_assets()
        self._valid_symbols = await self._get_valid_symbols()
        self._symbols_info = await self._get_symbols_info()
        return self

    def calc_proffit(self, alt_stable_price: float, ammount: float = 100.0):
        qty = (ammount / alt_stable_price) * settings.BINANCE_FEE_MULTIPLIER

    async def calc_proffits(self):
        for alt in self._tva.assets:
            try:
                alt_stable_symbol = f"{alt}{self.stable}"
                if alt_stable_symbol not in self._valid_symbols.symbols:
                    continue

                stable = await self._depths_crud.get(alt_stable_symbol)
                stable_ask_price = float(stable.asks[0][0])
                stable_bid_price = float(stable.bids[0][0])

                for stg in STRONG_ASSETS:
                    alt_strong_symbol = f"{alt}{stg}"
                    if alt_strong_symbol not in self._valid_symbols.symbols:
                        continue

                    strong = await self._depths_crud.get(alt_strong_symbol)
                    strong_ask_price = float(strong.asks[0][0])
                    strong_bid_price = float(strong.bids[0][0])

                    strong_stable = await self._depths_crud.get(
                        f"{stg}{self.stable}"
                    )

                    yield self.gap_model(
                        assets=f"{alt}-{stg}-{self.stable}",
                        alt=alt,
                        strong=stg,
                        stable=self.stable,
                        # value=round(strong_pcp - stable_pcp, 2)
                    )
            except NotFoundError:
                pass

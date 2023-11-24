import asyncio

import anyio
from tria_bot.services.tickers import TickerSvc

# ALT_ASSETS = (
#     "FDUSD",
#     "SOL",
#     "XRP",
#     "LINK",
#     "AVAX",
#     "SEI",
#     "HIFI",
#     "UNI",
#     "MATIC",
#     "DOGE",
# )


if __name__ == "__main__":

    # SYMBOLS = alt_combos(
    #     alt_asset="SOL",
    #     stable_assets=("USDT", )
    # )
    # SYMBOLS = strong_stable_combos(stable_assets=("USDT", ))
    # SYMBOLS = list(strong_alt_combos("BTC", ALT_ASSETS))
    # symbols = list(all_combos(alt_assets=ALT_ASSETS, stable_assets=('USDT',)))
    # print(symbols)
    asyncio.run(TickerSvc._subscribe())

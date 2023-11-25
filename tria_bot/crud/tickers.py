from tria_bot.crud.base import CRUDBase
from tria_bot.models.ticker import Ticker


class TickersCRUD(CRUDBase[Ticker]):
    model = Ticker

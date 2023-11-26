from tria_bot.crud.base import CRUDBase
from tria_bot.models.gap import Gap


class GapsCRUD(CRUDBase[Gap]):
    model = Gap



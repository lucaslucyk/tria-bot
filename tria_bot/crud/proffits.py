from tria_bot.crud.base import CRUDBase
from tria_bot.models.proffit import Proffit


class ProffitsCRUD(CRUDBase[Proffit]):
    model = Proffit

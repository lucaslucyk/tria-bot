from tria_bot.crud.base import CRUDBase
from tria_bot.models.depth import Depth


class DepthsCRUD(CRUDBase[Depth]):
    model = Depth

from tria_bot.crud.base import CRUDBase
from tria_bot.models.composite import TopVolumeAssets


class TopVolumeAssetsCRUD(CRUDBase[TopVolumeAssets]):
    model = TopVolumeAssets

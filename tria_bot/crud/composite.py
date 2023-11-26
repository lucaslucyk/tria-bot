from tria_bot.crud.base import CRUDBase
from tria_bot.models.composite import Symbol, TopVolumeAssets, ValidSymbols


class TopVolumeAssetsCRUD(CRUDBase[TopVolumeAssets]):
    model = TopVolumeAssets



class SymbolsCRUD(CRUDBase[Symbol]):
    model = Symbol


class ValidSymbolsCRUD(CRUDBase[ValidSymbols]):
    model = ValidSymbols
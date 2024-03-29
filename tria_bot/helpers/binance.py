from decimal import Decimal
from typing import Literal, Optional, Sequence, Union
from binance.helpers import round_step_size
from tria_bot.models.composite import Symbol
from decimal import Context


class Binance:
    def __init__(self, symbols: Optional[Sequence[Symbol]] = None, **kwargs):
        self._context = Context()
        self._symbols_info = {}
        if symbols != None:
            self._symbols_info = dict(self._map_symbols(symbols))

    @staticmethod
    def _map_symbols(symbols: Sequence[Symbol]):
        for symbol in symbols:
            yield symbol.symbol, symbol

    def format_float_positional(self, x: float, precision: int = 8):
        """
        Convert the given float to a string,
        without resorting to scientific notation
        """
        # ensure float
        x = float(x)
        self._context.prec = precision
        d1 = self._context.create_decimal(repr(x))
        return format(d1, "f")

    def _ffp(self, x: float, precision: int = 8):
        """
        Convert the given float to a string,
        without resorting to scientific notation
        """
        return self.format_float_positional(x=x, precision=precision)

    def _get_size(self, symbol: str, kind: Literal["step", "tick"]) -> float:
        """Get symbol size

        Args:
            symbol (str): Symbol str
            kind (Literal["step", "tick"]): Size kind

        Raises:
            KeyError: If symbol not found
            ValueError: If kind size not found

        Returns:
            float: Kind size
        """
        info = self._symbols_info.get(symbol, None)
        if not info:
            raise KeyError(f"Symbol {symbol} not found")
        kind_size = getattr(info, f"{kind}_size", None)
        if not kind_size:
            raise ValueError(f"Not valid {kind} size for symbol {symbol}")
        return float(kind_size)

    def get_step_size(self, symbol: str) -> float:
        return self._get_size(symbol=symbol, kind="step")

    def get_tick_size(self, symbol: str) -> float:
        return self._get_size(symbol=symbol, kind="tick")

    def _apply_size(
        self,
        symbol: str,
        kind: Literal["step", "tick"],
        value: Union[float, Decimal, str],
    ) -> float:
        """Get and apply symbol kind zize to a value

        Args:
            symbol (str): Symbol str
            kind (Literal["step", "tick"]): Size kind
            value (Union[float, Decimal, str]): Value to apply

        Returns:
            float: Applied size kind
        """
        kind_size = self._get_size(symbol=symbol, kind=kind)
        return round_step_size(quantity=value, step_size=kind_size)

    def apply_step_size(
        self, symbol: str, value: Union[float, Decimal, str]
    ) -> float:
        return self._apply_size(symbol=symbol, kind="step", value=value)

    def apply_tick_size(
        self,
        symbol: str,
        value: Union[float, Decimal, str],
    ) -> float:
        return self._apply_size(symbol=symbol, kind="tick", value=value)

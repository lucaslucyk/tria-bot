package binance_symbols

import (
	"fmt"

	"github.com/adshao/go-binance/v2"
	"github.com/lucaslucyk/tria-bot/shared/config"
	dbm "github.com/lucaslucyk/tria-bot/shared/models/db"
)

type Symbols struct {
	Combos []string
}

func NewCombo() *Symbols {
	symbols := Symbols{
		Combos: []string{},
	}

	stableCoin := config.Settings.StableCoin
	for _, strong := range config.Settings.StrongCoins {
		symbols.Combos = append(symbols.Combos, fmt.Sprintf("%s%s", strong, stableCoin))

		for _, alt := range config.Settings.AltCoins {
			symbols.Combos = append(symbols.Combos, fmt.Sprintf("%s%s", alt, strong))
			symbols.Combos = append(symbols.Combos, fmt.Sprintf("%s%s", alt, stableCoin))
		}
	}
	return &symbols
}

func (s *Symbols) ValidSymbols(symbols *[]binance.Symbol) []dbm.Symbol {
	var validSymbols []dbm.Symbol
	for _, symbol := range *symbols {
		for _, comboSymbol := range s.Combos {
			if symbol.Symbol == comboSymbol {
				dbSymbol := dbm.Symbol{
					Symbol:                   symbol.Symbol,
					Status:                   symbol.Status,
					BaseAsset:                symbol.BaseAsset,
					BaseAssetPrecision:       symbol.BaseAssetPrecision,
					QuoteAsset:               symbol.QuoteAsset,
					QuotePrecision:           symbol.QuotePrecision,
					QuoteAssetPrecision:      symbol.QuoteAssetPrecision,
					BaseCommissionPrecision:  symbol.BaseCommissionPrecision,
					QuoteCommissionPrecision: symbol.QuoteCommissionPrecision,
					OrderTypes:               symbol.OrderTypes,
					Filters: &dbm.Filters{
						Price:   symbol.PriceFilter(),
						LotSize: symbol.LotSizeFilter(),
					},
				}

				if dbSymbol.IsLimitAllowed() && dbSymbol.IsMarketAllowed() {
					validSymbols = append(validSymbols, dbSymbol)
				}
			}
		}
	}
	return validSymbols
}

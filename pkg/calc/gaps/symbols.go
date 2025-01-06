package gaps

import (
	"time"

	"github.com/lucaslucyk/tria-bot/shared/logger"
	dbm "github.com/lucaslucyk/tria-bot/shared/models/db"
	"github.com/lucaslucyk/tria-bot/shared/utils"
)

type AltCombos struct {
	Stable  *dbm.Symbol
	Strongs []*dbm.Symbol
}
type AssetCombos map[string]AltCombos

func (ac *AssetCombos) SetStable(asset string, symbol *dbm.Symbol) {
	if combo, ok := (*ac)[asset]; ok {
		(combo).Stable = symbol
		(*ac)[asset] = combo
	} else {
		(*ac)[asset] = AltCombos{
			Stable: symbol,
		}
	}
}

func (ac *AssetCombos) AddStrong(asset string, symbol *dbm.Symbol) {
	if combo, ok := (*ac)[asset]; ok {
		(combo).Strongs = append((combo).Strongs, symbol)
		(*ac)[asset] = combo
	} else {
		(*ac)[asset] = AltCombos{
			Strongs: []*dbm.Symbol{symbol},
		}
	}
}

func GetSymbols() (*[]*dbm.Symbol, error) {
	symbols, err := SymbolsRepo.List()
	if err != nil {
		return nil, err
	}

	if len(symbols) == 0 {
		logger.Info("No symbols yet, trying again in 3 seconds...")
		time.Sleep(3 * time.Second)
		return GetSymbols()
	}

	return &symbols, nil
}

func GetCombos(symbols *[]*dbm.Symbol) *AssetCombos {
	combos := AssetCombos{}

	for _, symbol := range *symbols {
		baseKind := utils.GetAssetKind(symbol.BaseAsset)
		if baseKind != utils.AltCoin {
			continue
		}

		quoteKind := utils.GetAssetKind(symbol.QuoteAsset)
		if quoteKind == utils.StableCoin {
			combos.SetStable(symbol.BaseAsset, symbol)
		}

		if quoteKind == utils.StrongCoin {
			combos.AddStrong(symbol.BaseAsset, symbol)
		}
	}
	return &combos
}

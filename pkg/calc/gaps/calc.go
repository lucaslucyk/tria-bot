package gaps

import (
	"github.com/lucaslucyk/tria-bot/shared/logger"
	db_models "github.com/lucaslucyk/tria-bot/shared/models/db"
	dbm "github.com/lucaslucyk/tria-bot/shared/models/db"
	"github.com/lucaslucyk/tria-bot/shared/utils/parse"
)

func Calculate(combos *AssetCombos) {
	logger.Debug("Refreshing gaps...")
	var t db_models.Ticker
	tPrefix := t.KeyPrefix()

	for altcoin, combo := range *combos {
		stbKey := tPrefix + combo.Stable.Symbol
		altStbTicker, err := TickersRepo.Get(stbKey)
		if err != nil {
			logger.Error("Error getting stable ticker: %v", err)
			continue
		}

		stbPcp, err := parse.ToFloat(altStbTicker.PriceChangePercent, 2)
		if err != nil {
			logger.Error("Error parsing stable ticker: %v", err)
			continue
		}

		for _, ss := range combo.Strongs {
			stgKey := tPrefix + ss.Symbol
			altStgTicker, err := TickersRepo.Get(stgKey)
			if err != nil {
				logger.Error("Error getting strong ticker: %v", err)
				continue
			}

			stgPcp, err := parse.ToFloat(altStgTicker.PriceChangePercent, 2)
			if err != nil {
				logger.Error("Error parsing strong ticker: %v", err)
				continue
			}

			gap := dbm.Gap{
				AltCoin:    altcoin,
				StrongCoin: ss.QuoteAsset,
				StableCoin: combo.Stable.QuoteAsset,
				Value:      parse.Round(stgPcp-stbPcp, 2),
			}

			if err := GapsRepo.Save(gap); err != nil {
				logger.Error("Error saving gap: %v", err)
			}
		}
	}
}

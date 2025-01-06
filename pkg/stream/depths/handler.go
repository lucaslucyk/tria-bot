package depths

import (
	"github.com/adshao/go-binance/v2"
	"github.com/adshao/go-binance/v2/common"
	"github.com/lucaslucyk/tria-bot/shared/logger"
	dbm "github.com/lucaslucyk/tria-bot/shared/models/db"
)

func GetPriceLevels(bpl []common.PriceLevel) *[]dbm.PriceLevel {
	var pl []dbm.PriceLevel

	for _, v := range bpl {
		pl = append(pl, dbm.PriceLevel{Price: v.Price})
	}

	return &pl
}

func DepthEventHandler(event *binance.WsPartialDepthEvent) {
	logger.Debug(
		"Symbol: %s, Best Ask: %s, Best Bid: %s",
		event.Symbol,
		event.Asks[0].Price,
		event.Bids[0].Price,
	)

	t := dbm.Depth{
		Symbol:      event.Symbol,
		Bids:        GetPriceLevels(event.Bids),
		Asks:        GetPriceLevels(event.Asks),
		TopAskPrice: event.Asks[0].Price,
		TopBidPrice: event.Bids[0].Price,
	}

	if err := Repository.Save(t); err != nil {
		logger.Error("Error saving ticker: %v", err)
	}
}

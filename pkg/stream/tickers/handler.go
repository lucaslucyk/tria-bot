package tickers

import (
	"github.com/adshao/go-binance/v2"
	"github.com/lucaslucyk/tria-bot/shared/logger"
	dbm "github.com/lucaslucyk/tria-bot/shared/models/db"
)

func TickerEventHandler(event *binance.WsMarketStatEvent) {
	logger.Info(
		"Symbol: %s, PCP: %s",
		event.Symbol,
		event.PriceChangePercent,
	)

	t := dbm.Ticker{
		Symbol:             event.Symbol,
		PriceChange:        event.PriceChange,
		PriceChangePercent: event.PriceChangePercent,
	}

	if err := Repository.Save(t); err != nil {
		logger.Error("Error saving ticker: %v", err)
	}
}

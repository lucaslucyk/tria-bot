package db_models

import "github.com/lucaslucyk/tria-bot/shared/config"

type Ticker struct {
	Symbol             string `json:"s"`
	PriceChange        string `json:"p"`
	PriceChangePercent string `json:"P"`
}

func (t Ticker) DbIndex() int {
	return config.Settings.RedisDefaultDb
}

func (t Ticker) Pattern() string {
	return "tickers:*"
}

func (t Ticker) KeyPrefix() string {
	return "tickers:"
}

func (t Ticker) Key() string {
	return t.KeyPrefix() + t.Symbol
}

package db_models

import (
	"github.com/lucaslucyk/tria-bot/shared/config"
)

type PriceLevel struct {
	Price    string `json:"p"`
	Quantity string `json:"q"`
}

type Depth struct {
	Symbol      string        `json:"s"`
	Bids        *[]PriceLevel `json:"b"`
	Asks        *[]PriceLevel `json:"a"`
	TopAskPrice string        `json:"tap"`
	TopBidPrice string        `json:"tbp"`
}

func (d Depth) DbIndex() int {
	return config.Settings.RedisDefaultDb
}

func (d Depth) Pattern() string {
	return "depths:*"
}

func (d Depth) KeyPrefix() string {
	return "depths:"
}

func (d Depth) Key() string {
	return d.KeyPrefix() + d.Symbol
}

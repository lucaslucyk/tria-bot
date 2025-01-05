package db_models

import (
	"github.com/adshao/go-binance/v2"
	"github.com/lucaslucyk/tria-bot/shared/config"
)

type Filters struct {
	Price   *binance.PriceFilter   `json:"price"`
	LotSize *binance.LotSizeFilter `json:"lotSize"`
}

type Symbol struct {
	Symbol                   string   `json:"symbol"`
	Status                   string   `json:"status"`
	BaseAssetPrecision       int      `json:"baseAssetPrecision"`
	QuoteAsset               string   `json:"quoteAsset"`
	QuotePrecision           int      `json:"quotePrecision"`
	QuoteAssetPrecision      int      `json:"quoteAssetPrecision"`
	BaseCommissionPrecision  int32    `json:"baseCommissionPrecision"`
	QuoteCommissionPrecision int32    `json:"quoteCommissionPrecision"`
	OrderTypes               []string `json:"orderTypes"`

	Filters *Filters `json:"filters"`
}

func (t Symbol) DbIndex() int {
	return config.Settings.RedisDefaultDb
}

func (t Symbol) Pattern() string {
	return "symbols:*"
}

func (t Symbol) KeyPrefix() string {
	return "symbols:"
}

func (t Symbol) Key() string {
	return t.KeyPrefix() + t.Symbol
}

func (t *Symbol) IsMarketAllowed() bool {
	for _, orderType := range t.OrderTypes {
		if binance.OrderType(orderType) == binance.OrderTypeMarket {
			return true
		}
	}
	return false
}

func (t *Symbol) IsLimitAllowed() bool {
	for _, orderType := range t.OrderTypes {
		if binance.OrderType(orderType) == binance.OrderTypeLimit {
			return true
		}
	}
	return false
}

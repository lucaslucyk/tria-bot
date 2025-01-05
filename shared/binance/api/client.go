package binance_api

import (
	"context"

	"github.com/adshao/go-binance/v2"
)

type BinanceClient struct {
	Client *binance.Client
	ctx    context.Context
}

func NewPublicClient() *BinanceClient {
	return &BinanceClient{
		Client: binance.NewClient("", ""),
		ctx:    context.Background(),
	}
}

func (c *BinanceClient) ExchangeSymbols() (*[]binance.Symbol, error) {
	ei, err := c.Client.NewExchangeInfoService().Do(c.ctx)
	if err != nil {
		return nil, err
	}

	return &ei.Symbols, err
}

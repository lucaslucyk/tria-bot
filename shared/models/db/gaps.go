package db_models

import "github.com/lucaslucyk/tria-bot/shared/config"

type Gap struct {
	AltCoin    string  `json:"alt"`
	StrongCoin string  `json:"strong"`
	StableCoin string  `json:"stable"`
	Value      float64 `json:"value"`
}

func (t *Gap) ExtendedSymbol() string {
	return t.AltCoin + t.StrongCoin + t.StableCoin
}

func (t Gap) DbIndex() int {
	return config.Settings.RedisDefaultDb
}

func (t Gap) Pattern() string {
	return "gaps:*"
}

func (t Gap) KeyPrefix() string {
	return "gaps:"
}

func (t Gap) Key() string {
	return t.KeyPrefix() + t.ExtendedSymbol()
}

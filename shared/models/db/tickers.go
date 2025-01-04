package db_models

type Ticker struct {
	Symbol             string `json:"s"`
	PriceChange        string `json:"p"`
	PriceChangePercent string `json:"P"`
}

func (t Ticker) DbIndex() int {
	return 0
}

func (t Ticker) Pattern() string {
	return "tickers:*"
}

func (t Ticker) Key() string {
	return "tickers:" + t.Symbol
}

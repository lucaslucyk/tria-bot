package tickers

import (
	tickers_pkg "github.com/lucaslucyk/tria-bot/pkg/stream/tickers"
)

func Start() {
	// start ticker service
	tickers_pkg.Start()
}

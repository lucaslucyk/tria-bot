package tickers

import (
	"os"
	"os/signal"
	"syscall"

	"github.com/adshao/go-binance/v2"
	"github.com/lucaslucyk/tria-bot/shared/logger"
	dbm "github.com/lucaslucyk/tria-bot/shared/models/db"
	"github.com/lucaslucyk/tria-bot/shared/redis"
)

var Repository *redis.Repository[dbm.Ticker]

func Start() {
	Repository = redis.NewRepository[dbm.Ticker]()
	Symbols, err := GetSymbols()
	if err != nil {
		logger.Error("Error getting symbols: %v", err)
		return
	}

	errHandler := func(err error) {
		logger.Error("Error: %v\n", err)
	}

	// Conectar al stream de tickers para un símbolo específico (por ejemplo, BTCUSDT)
	doneC, stopC, err := binance.WsCombinedMarketStatServe(
		Symbols,
		TickerEventHandler,
		errHandler,
	)
	if err != nil {
		logger.Error("Error to start WebSocket: %v", err)
		// log.Fatalf("Error al iniciar WebSocket: %v", err)
	}

	// Esperar señales de interrupción (Ctrl+C)
	signalC := make(chan os.Signal, 1)
	signal.Notify(signalC, os.Interrupt, syscall.SIGTERM)
	<-signalC

	// Detener el WebSocket
	stopC <- struct{}{}
	<-doneC

	logger.Info("WebSocket stopped!")
}

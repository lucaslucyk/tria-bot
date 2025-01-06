package depths

import (
	"os"
	"os/signal"
	"syscall"

	"github.com/adshao/go-binance/v2"
	"github.com/lucaslucyk/tria-bot/shared/logger"
	dbm "github.com/lucaslucyk/tria-bot/shared/models/db"
	"github.com/lucaslucyk/tria-bot/shared/redis"
)

var Repository *redis.Repository[dbm.Depth]

// Symbols    []string

func Start() {
	Repository = redis.NewRepository[dbm.Depth]()
	Symbols, err := GetSymbols()
	if err != nil {
		logger.Error("Error getting symbols: %v", err)
		return
	}
	logger.Info("Symbols: %v", Symbols)
	if len(Symbols) == 0 {
		logger.Error("No symbols found")
		return
	}

	symbolLevels := func() map[string]string {
		symbolsMap := map[string]string{}
		for _, symbol := range Symbols {
			symbolsMap[symbol] = "5"
		}
		return symbolsMap
	}()

	errHandler := func(err error) {
		logger.Error("Error: %v\n", err)
	}

	// Conectar al stream de tickers para un símbolo específico (por ejemplo, BTCUSDT)
	doneC, stopC, err := binance.WsCombinedPartialDepthServe(symbolLevels, DepthEventHandler, errHandler)
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

package tickers

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/adshao/go-binance/v2"
	"github.com/lucaslucyk/tria-bot/shared/logger"
)

func Start() {
	// Crear un cliente WebSocket
	wsHandler := func(event *binance.WsMarketStatEvent) {
		logger.Info(
			"Symbol: %s, PCP: %s",
			event.Symbol,
			event.PriceChangePercent,
		)
	}

	errHandler := func(err error) {
		logger.Error("Error: %v\n", err)
		// log.Printf("Error: %v\n", err)
	}

	// Conectar al stream de tickers para un símbolo específico (por ejemplo, BTCUSDT)
	doneC, stopC, err := binance.WsCombinedMarketStatServe(
		[]string{"BTCUSDT"},
		wsHandler,
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

	fmt.Println("WebSocket cerrado.")
}

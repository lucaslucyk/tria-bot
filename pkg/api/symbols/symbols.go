package symbols

import (
	"os"
	"os/signal"
	"syscall"
	"time"

	binance_api "github.com/lucaslucyk/tria-bot/shared/binance/api"
	binance_symbols "github.com/lucaslucyk/tria-bot/shared/binance/db"
	"github.com/lucaslucyk/tria-bot/shared/logger"
	dbm "github.com/lucaslucyk/tria-bot/shared/models/db"
	"github.com/lucaslucyk/tria-bot/shared/redis"
)

var Repository *redis.Repository[dbm.Symbol]

func Start() {
	logger.Info("Initializing symbols repository")
	Repository = redis.NewRepository[dbm.Symbol]()
	bc := binance_api.NewPublicClient()
	symbolsLoop(bc)
}

func symbolsLoop(client *binance_api.BinanceClient) {
	// exec 1 time
	RefreshSymbols(client)

	// Crear un canal para capturar señales de interrupción (Ctrl-C)
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Crear un ticker para ejecutar cada 60 segundos
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()

	// Iniciar el proceso en un bucle infinito que solo se detiene cuando recibe una señal de interrupción
	for {
		select {
		case <-sigChan:
			logger.Info("Received interrupt signal. Stopping the symbol refresh process.")
			return
		case <-ticker.C:
			// Ejecutar RefreshSymbols en una goroutine sin bloquear el bucle principal
			go RefreshSymbols(client)
		}
	}
}

func RefreshSymbols(client *binance_api.BinanceClient) {
	logger.Info("Refreshing symbols repository")
	symbols, err := client.ExchangeSymbols()
	if err != nil {
		logger.Error("Error getting symbols: %v", err)
	}

	validSymbols := binance_symbols.NewCombo().ValidSymbols(symbols)

	for _, symbol := range validSymbols {
		if err := Repository.Save(symbol); err != nil {
			logger.Error("Error saving symbol: %v", err)
		}
	}

	logger.Info("Symbols refreshed successfully!")
}

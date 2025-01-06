package gaps

import (
	"os"
	"os/signal"
	"syscall"

	"github.com/lucaslucyk/tria-bot/shared/logger"
)

func StartCalcLoop(combos *AssetCombos) {
	// Crear un canal para capturar señales de interrupción (Ctrl-C)
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Iniciar el proceso en un bucle infinito que solo se detiene cuando recibe una señal de interrupción
	for {
		select {
		case <-sigChan:
			logger.Info("Received interrupt signal. Stopping the symbol refresh process.")
			return
		default:
			// Ejecutar RefreshSymbols en una goroutine sin bloquear el bucle principal
			Calculate(combos)
		}
	}
}

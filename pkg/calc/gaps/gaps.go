package gaps

import (
	"github.com/lucaslucyk/tria-bot/shared/logger"
)

func Start() {
	logger.Info("Starting gaps calculator...")
	InitRepos()

	symbols, err := GetSymbols()
	if err != nil {
		logger.Error("Error getting symbols: %v", err)
		return
	}
	logger.Info("Symbols: %v", symbols)
	combos := GetCombos(symbols)

	StartCalcLoop(combos)
	logger.Info("Gaps calculator stopped!")
}

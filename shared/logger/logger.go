package logger

import (
	"fmt"

	"go.uber.org/zap"
)

var Logger *zap.SugaredLogger

// InitLogger inicializa el logger con el nivel de log y configuración deseada.
func Init(debug bool) {
	var baseLogger *zap.Logger
	var err error

	if debug {
		baseLogger, err = zap.NewDevelopment() // Configuración para desarrollo (legible).
	} else {
		baseLogger, err = zap.NewProduction() // Configuración para producción (JSON).
	}

	if err != nil {
		panic("Could not create logger: " + err.Error())
	}

	// Crear un SugaredLogger para una sintaxis más simple.
	Logger = baseLogger.Sugar()
}

// Info registra mensajes informativos.
func Info(message string, args ...any) {
	Logger.Info(fmt.Sprintf(message, args...))
}

// Debug registra mensajes de depuración.
func Debug(message string, args ...any) {
	Logger.Debug(fmt.Sprintf(message, args...))
}

// Error registra mensajes de error.
func Error(message string, args ...any) {
	Logger.Error(fmt.Sprintf(message, args...))
}

// Sync asegura que todos los logs se escriban antes de cerrar la aplicación.
func Sync() {
	_ = Logger.Sync()
}

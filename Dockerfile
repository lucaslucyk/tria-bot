# Etapa 1: Construcción
FROM docker.io/golang:1.23-bookworm AS builder

ENV CGO_ENABLED=0 \
    GOOS=linux \
    GOARCH=amd64

# Establecer el directorio de trabajo
WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

# Copiar el código fuente al contenedor
COPY . .
RUN go build -o tria-bot ./cmd

# Compilar el binario
# RUN go mod tidy && \
#     go build -o tria-bot ./cmd

# Etapa 2: Ejecución
FROM debian:bookworm-slim AS runtime

RUN apt-get update && apt-get install -y \
    libc6 ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear un directorio para la aplicación
WORKDIR /app

# Copiar el binario desde la etapa de construcción
COPY --from=builder /app/tria-bot .

RUN chmod +x /app/tria-bot

# Configurar el comando de inicio
CMD ["./tria-bot"]

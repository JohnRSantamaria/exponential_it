FROM python:3.13-alpine
# Directorio de trabajo
WORKDIR /app
# Configuración de entorno
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Instalar dependencias necesarias para compilar y correr
RUN apk update && apk upgrade --no-cache && apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    openssl-dev \
    build-base \
    python3-dev \
    libpq \
    bash \
    netcat-openbsd \
    && pip install --upgrade pip

# Copiar archivo de dependencias e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto (incluyendo scripts)
COPY . .

# Asegurar permisos de ejecución
RUN chmod +x /app/scripts/entrypoint.sh \
    && addgroup -S appgroup \
    && adduser -S appuser -G appgroup \
    && chown -R appuser:appgroup /app

USER appuser

# Comando por defecto (puede ser sobreescrito por docker-compose)
CMD ["sh", "/app/scripts/entrypoint.sh"]
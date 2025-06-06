# Usa una versión estable
FROM python:3.13-alpine

# Directorio de trabajo
WORKDIR /app

# Configuraciones de entorno
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Instala dependencias del sistema necesarias para compilar e instalar paquetes
RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    openssl-dev \
    build-base \
    python3-dev \
    libpq \
    bash \
    && pip install --upgrade pip

# Copiar requirements y paquetes Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código, incluyendo el wait-for-it.sh
COPY . .

# Dar permisos de ejecución al script de espera
RUN chmod +x ./scripts/wait-for-it.sh
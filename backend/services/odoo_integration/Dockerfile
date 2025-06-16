FROM python:3.13-alpine

# Establece el directorio de trabajo
WORKDIR /app

# Permite pasar el token desde el build
ARG GITHUB_TOKEN
ENV GITHUB_TOKEN=${GITHUB_TOKEN}

# Instala compiladores y librerías necesarias para paquetes con C extensions
RUN apk add --no-cache \
    build-base \
    gcc \
    musl-dev \
    libffi-dev \
    libc-dev

# Actualiza pip y herramientas de build
RUN python -m pip install --upgrade pip setuptools wheel

# Copia primero solo el requirements.txt para aprovechar el cache
COPY requirements.txt .

# Instala dependencias usando el token de GitHub
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código del proyecto
COPY . .

# Expone el puerto de la app
EXPOSE 8004

# Comando por defecto
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]

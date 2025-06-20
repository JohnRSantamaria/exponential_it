FROM python:3.13-alpine

# Establece el directorio de trabajo
WORKDIR /app

# Instala compiladores y librerías necesarias para paquetes con C extensions
RUN apk add --no-cache \
    build-base \
    gcc \
    musl-dev \
    libffi-dev \
    libc-dev

# Actualiza pip y herramientas de build
RUN python -m pip install --upgrade pip setuptools wheel

# Copia primero solo el requirements.txt para aprovechar el cache de Docker
COPY requirements.txt .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código del proyecto
COPY . .

# Expone el puerto de la app
EXPOSE 8004

# Comando por defecto
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]

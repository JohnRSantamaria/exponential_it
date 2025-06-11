#!/bin/sh
set -e

# Cargar variables desde .env si no las inyecta Docker directamente
export $(grep -v '^#' /app/.env | xargs) || true

# Extraer host y puerto de DATABASE_PROD
DB_URL=${DATABASE_PROD}
AFTER_AT=$(echo "$DB_URL" | awk -F@ '{print $2}' | awk -F/ '{print $1}')
DB_HOST=$(echo "$AFTER_AT" | cut -d: -f1)
DB_PORT=$(echo "$AFTER_AT" | cut -s -d: -f2)
DB_PORT=${DB_PORT:-5432}

# Validación defensiva
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
  echo "❌ No se pudo extraer DB_HOST o DB_PORT de DATABASE_PROD"
  echo "🔍 Valor de DATABASE_PROD: $DB_URL"
  exit 1
fi

# Esperar a que el puerto esté disponible
echo "🌐 Esperando a la base de datos en $DB_HOST:$DB_PORT..."

for i in $(seq 1 30); do
  if nc -z "$DB_HOST" "$DB_PORT"; then
    echo "✅ DB disponible"
    break
  fi
  echo -n "."
  sleep 1
done

# Validación final solo si aún no se conectó
if ! nc -z "$DB_HOST" "$DB_PORT"; then
  echo "\n❌ Timeout: no se pudo conectar a $DB_HOST:$DB_PORT"
  exit 1
fi

echo "🛠️ Ejecutando migraciones..."
python manage.py migrate

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "🚀 Iniciando Gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --access-logfile - \
  --error-logfile -

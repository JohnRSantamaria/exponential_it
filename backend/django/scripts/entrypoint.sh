#!/bin/sh
echo "📌 Entrypoint iniciado"

export $(grep -v '^#' /app/.env | xargs) || true

echo "🌍 DEBUG=$DEBUG"

if [ "$DEBUG" = "False" ]; then
  echo "🚀 Entorno producción"
  DB_URL=${DATABASE_PROD}
else
  echo "🧪 Entorno desarrollo"
  DB_URL=${DATABASE_LOCAL}
fi

AFTER_AT=$(echo "$DB_URL" | awk -F@ '{print $2}' | awk -F/ '{print $1}')
DB_HOST=$(echo "$AFTER_AT" | cut -d: -f1)
DB_PORT=$(echo "$AFTER_AT" | cut -s -d: -f2)
DB_PORT=${DB_PORT:-5432}

if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
  echo "❌ No se pudo extraer DB_HOST o DB_PORT de la URL seleccionada"
  echo "🔍 Valor de DB_URL: $DB_URL"
  exit 1
fi

echo "🌐 Esperando a la base de datos en $DB_HOST:$DB_PORT..."
for i in $(seq 1 30); do
  if nc -z "$DB_HOST" "$DB_PORT"; then
    echo "✅ DB disponible"
    break
  fi
  echo -n "."
  sleep 1
done

if ! nc -z "$DB_HOST" "$DB_PORT"; then
  echo "\n❌ Timeout: no se pudo conectar a $DB_HOST:$DB_PORT"
  exit 1
fi

echo "🛠️ Ejecutando migraciones..."
python manage.py migrate

if [ "$DEBUG" = "False" ]; then
  STATIC_ROOT=${STATIC_ROOT:-/app/config/staticfiles}
  echo "📦 Recolectando archivos estáticos en: $STATIC_ROOT"

  echo "🔧 Ajustando permisos de STATIC_ROOT"
  mkdir -p "$STATIC_ROOT"
  chown -R appuser:appgroup "$STATIC_ROOT" || echo "⚠️ No se pudo cambiar el dueño"
  chmod -R 755 "$STATIC_ROOT"

  python manage.py collectstatic --noinput
else
  echo "🧪 Entorno de desarrollo: se omite collectstatic"
fi

echo "🚀 Iniciando Gunicorn..."
WORKERS=3

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers $WORKERS \
  --access-logfile - \
  --error-logfile -

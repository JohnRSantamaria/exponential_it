#!/bin/bash

echo "🧼 Borrando archivos de migración..."

find backend/django/applications -type d -name "migrations" | while read dir; do
    echo "→ Limpiando $dir"
    find "$dir" -type f ! -name "__init__.py" -name "*.py" -delete
    find "$dir" -type f -name "*.pyc" -delete
done

echo "🧨 Deteniendo y eliminando contenedores y volúmenes..."
docker compose down -v

echo "🚀 Reconstruyendo contenedores..."
docker compose up --build -d

echo "📌 Recuerda ejecutar después:"
echo "   docker compose exec admin_django python manage.py makemigrations"
echo "   docker compose exec admin_django python manage.py migrate"

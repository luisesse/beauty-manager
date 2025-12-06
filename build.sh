#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Instalar requerimientos
pip install -r requirements.txt

# 2. Recolectar archivos estáticos (CSS/JS)
python manage.py collectstatic --no-input

# 3. Aplicar migraciones a la base de datos de la nube
python manage.py migrate
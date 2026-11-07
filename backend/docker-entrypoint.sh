#!/bin/sh
set -e

# Crea las tablas y carga los datos de demo (idempotente: no duplica nada).
if [ "${SEED_DEMO:-true}" = "true" ]; then
  echo "Cargando datos de demo..."
  python scripts/seed_dev.py
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000

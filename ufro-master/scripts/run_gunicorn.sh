#!/usr/bin/env bash
export PYTHONUNBUFFERED=1
export UVICORN_WORKERS=${UVICORN_WORKERS:-4}
gunicorn api.app:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8300 --workers $UVICORN_WORKERS
## por si se usa en linux
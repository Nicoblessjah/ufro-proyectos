#!/usr/bin/env bash
export $(grep -v '^#' .env | xargs)
exec gunicorn -w 2 -b 0.0.0.0:${PORT:-5000} api.app:app
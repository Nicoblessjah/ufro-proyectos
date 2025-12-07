# UFRO Master Orchestrator (PP3)

Agente orquestador que integra:

- PP2: verificador personal (`/verify`)
- PP1: RAG normativa UFRO (`/ask`)
- MongoDB: logging y métricas
- API REST (`/identify-and-answer`, `/metrics/*`, `/healthz`)

## Requisitos

- Python 3.11
- MongoDB (local o Atlas)
- PP2 (`me-verifier`) corriendo en `http://127.0.0.1:5000/verify`
- PP1 (`ufro-assistant`) corriendo en `http://127.0.0.1:8200/ask`

## Instalación

```bash
cd ufro-master
py -3.11 -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env

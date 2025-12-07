UFRO – Evaluación PP1, PP2, PP3 (Orquestación con FastAPI + n8n + MongoDB)

Autor: Nicolás Olivero
Año: 2025

Este repositorio contiene la implementación completa de los servicios PP1, PP2 y PP3, junto con su integración mediante n8n, MongoDB y la documentación técnica correspondiente.

Descripción General del Proyecto

El sistema implementa un flujo de identificación biométrica (PP2), consulta normativa académica (PP1) y un orquestador (PP3) que combina ambos servicios, valida solicitud de usuario, registra actividad y expone un endpoint unificado.

Además, se incluye un workflow automatizado en n8n que replica la función del PP3 mediante nodos visuales para enviar imágenes, procesarlas y entregar una respuesta conjunta.

Estructura del Repositorio
ufro-proyectos/
│
├── me-verifier/             # Código del modelo biométrico PP2
│
├── ufro-assistant/          # Código del modelo RAG PP1
│
├── ufro-master/             # Orquestador PP3 (FastAPI)
│   ├── api/
│   ├── orchestrator/
│   ├── db/
│   ├── .env.example         # Archivo de ejemplo sin secretos
│   ├── requirements.txt
│
├── docs/
│   └── Informe tecnico.pdf
│
├── n8n/
│   └── workflow_pp3.json    # Workflow exportado desde n8n
│
└── README.md

Requerimientos
Software necesario

Python 3.10+

MongoDB Community Edition

n8n (CLI o Desktop)

Git

curl (para pruebas)

Instalación y Ejecución de los Servicios
PP1 – Servicio RAG (Normativa UFRO)
cd ufro-assistant
pip install -r requirements.txt
uvicorn app:app --reload --port 8200


Endpoint principal:

POST http://127.0.0.1:8200/ask

PP2 – Servicio Biométrico (Verificador de identidad)
cd me-verifier
pip install -r requirements.txt
uvicorn app:app --port 5000


Endpoint principal:

POST http://127.0.0.1:5000/verify

PP3 – Orquestador

Crear el archivo .env basado en .env.example:

MONGO_URI=mongodb://localhost:27017
DB_NAME=ufro_master
API_TOKEN=supersecreto123
PP1_URL=http://127.0.0.1:8200/ask
PP2_URL=http://127.0.0.1:5000/verify


Instalar dependencias y ejecutar:

cd ufro-master
pip install -r requirements.txt
uvicorn api.app:app --reload --port 8300


Endpoints clave:

Ruta	Descripción
POST /identify-and-answer	Orquestación completa
GET /metrics/summary	Métricas generales
GET /healthz	Estado del servicio
Inicializar índices en MongoDB
python db/ensure_indexes.py

Workflow de n8n

El archivo exportado se encuentra en:

n8n/workflow_pp3.json

Para importarlo:

Abrir n8n → Import Workflow

Seleccionar workflow_pp3.json

Activar el workflow

Usar el webhook mostrado en pantalla

Ejemplo de prueba con curl
curl -X POST "http://localhost:5678/webhook-test/pp3-webhook" \
 -F "image=@C:/ruta/a/tu/imagen.jpg" \
 -F "question=¿Cuántos días tengo para retractarme de la matrícula?"


Ejemplo de respuesta:

{
  "decision": "identified",
  "identity": "{...}",
  "normativa_answer": "No se encuentra en la normativa...",
  "timing_ms": "270.8"
}


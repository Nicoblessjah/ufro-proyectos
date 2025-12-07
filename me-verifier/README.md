# Verificador de identidad por imagen

Proyecto simple para verificar si una foto corresponde a “ME”. Usa embeddings faciales y un clasificador ligero. Funciona en CPU (sin GPU) y trae API local, scripts de entrenamiento y evaluación.

---

## Requisitos

- Python **3.11** o superior  
- Windows / macOS / Linux  
- Dependencias en `requirements.txt` (CPU only)

---

## Instalación

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
copy .env.example .env

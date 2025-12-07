# api/app.py
import io
import os
import time
import math
from PIL import Image
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import joblib
import numpy as np
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1

# --- Carga de configuración ---
load_dotenv()
MODEL_PATH   = os.getenv("MODEL_PATH", "models/model.joblib")
THRESHOLD    = float(os.getenv("THRESHOLD", "0.75"))
DEVICE       = torch.device(os.getenv("DEVICE", "cpu"))
MODEL_VERSION= os.getenv("MODEL_VERSION", "me-verifier-v1")
MAX_MB       = int(os.getenv("MAX_MB", "5"))

# --- App Flask ---
app = Flask(__name__)

# --- Modelos (se cargan una sola vez) ---
mtcnn  = MTCNN(image_size=160, margin=14, post_process=True, device=DEVICE)  # keep_all=False por defecto
resnet = InceptionResnetV1(pretrained="vggface2").eval().to(DEVICE)
clf    = joblib.load(MODEL_PATH)

def _ext_ok(filename: str) -> bool:
    fn = filename.lower()
    return fn.endswith(".jpg") or fn.endswith(".jpeg") or fn.endswith(".png")

@app.get("/healthz")
def healthz():
    return {"status": "ok", "model_version": MODEL_VERSION}

@app.post("/verify")
def verify():
    t0 = time.time()

    # Validaciones básicas
    if "image" not in request.files:
        return jsonify({"error": 'campo "image" requerido'}), 400

    f = request.files["image"]
    if not f or f.filename == "":
        return jsonify({"error": "archivo vacío"}), 400

    if not _ext_ok(f.filename):
        return jsonify({"error": "solo image/jpeg o image/png"}), 415

    # Límite de tamaño
    try:
        pos = f.stream.tell()
        f.stream.seek(0, os.SEEK_END)
        size_mb = f.stream.tell() / (1024 * 1024)
        f.stream.seek(pos, os.SEEK_SET)
        if size_mb > MAX_MB:
            return jsonify({"error": f"archivo demasiado grande (> {MAX_MB} MB)"}), 413
    except Exception:
        # Si no se puede medir, seguimos igual (Flask puede manejar tamaños por config si quieres)
        pass

    # Abrir imagen
    try:
        raw = f.read()
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return jsonify({"error": "imagen inválida"}), 400

    # Detectar y alinear rostro (tensor CHW en rango [0,1])
    face = mtcnn(img)
    if face is None:
        return jsonify({"error": "no se detectó rostro"}), 422

    # Normalización consistente con embeddings.py: (x - 0.5)/0.5
    x = face.unsqueeze(0).to(DEVICE)            # [1,3,160,160] en [0,1]
    x = (x - 0.5) / 0.5

    # Extraer embedding 512D
    with torch.no_grad():
        emb = resnet(x).cpu().numpy()           # shape (1,512)

    # Puntaje del clasificador -> [0,1]
    try:
        # Regresión logística u otro modelo con predict_proba
        score = float(clf.predict_proba(emb)[:, 1][0])
    except Exception:
        # LinearSVC/otros sin predict_proba: usar sigmoide sobre decision_function
        df = float(clf.decision_function(emb)[0])
        score = 1.0 / (1.0 + math.exp(-df))     # mapea a (0,1) como proxy

    is_me = bool(score >= THRESHOLD)
    elapsed_ms = round((time.time() - t0) * 1000.0, 1)

    return jsonify({
        "model_version": MODEL_VERSION,
        "is_me": is_me,
        "score": round(score, 4),
        "threshold": THRESHOLD,
        "timing_ms": elapsed_ms
    }), 200

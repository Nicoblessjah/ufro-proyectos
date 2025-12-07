from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from uuid import uuid4
from time import perf_counter
from datetime import datetime
import hashlib
import yaml
from pathlib import Path

from db.mongo import get_db, get_settings
from db.queries import (
    metrics_summary,
    metrics_by_user_type,
    metrics_decisions,
    metrics_services,
)
from orchestrator.pp2_client import verify_all, get_settings as get_pp2_settings
from orchestrator.pp1_client import ask_normativa
from orchestrator.fuse import fuse_candidates
from orchestrator.schemas import IdentifyAndAnswerResponse

MAX_MB = 5.0
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}

app = FastAPI(title="UFRO Master Orchestrator PP3", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def require_token(authorization: Optional[str] = Header(None)):
    """
    Middleware simple de autenticación via Bearer token.
    Usa api_token definido en db.mongo.Settings (archivo .env).
    """
    settings = get_settings()
    if not settings.api_token:
        return

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")

    token = authorization.split(" ", 1)[1]
    if token != settings.api_token:
        raise HTTPException(status_code=403, detail="Token inválido")


@app.post(
    "/identify-and-answer",
    response_model=IdentifyAndAnswerResponse,
    dependencies=[Depends(require_token)],
)
async def identify_and_answer(
    image: UploadFile = File(...),
    question: Optional[str] = Form(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_type: Optional[str] = Header(None, alias="X-User-Type"),
):
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="solo image/jpeg o image/png")

    contents = await image.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_MB:
        raise HTTPException(status_code=413, detail="archivo demasiado grande (> 5 MB)")

    image_hash = hashlib.sha256(contents).hexdigest()

    request_id = str(uuid4())
    t0 = perf_counter()

    candidates, pp2_summary = await verify_all(contents, request_id)
    pp2_settings = get_pp2_settings()
    decision, identity = fuse_candidates(
        candidates, margin=pp2_settings.FUSE_MARGIN
    )

    normativa_answer = None
    if question:
        normativa_answer = await ask_normativa(question, request_id)

    timing_ms = round((perf_counter() - t0) * 1000.0, 2)

    db = await get_db()
    user_doc = {
        "id": x_user_id or "anon",
        "type": x_user_type or "external",
        "role": "basic",
    }

    access_doc = {
        "request_id": request_id,
        "ts": datetime.utcnow(),
        "route": "/identify-and-answer",
        "user": user_doc,
        "input": {
            "has_image": True,
            "has_question": bool(question),
            "image_hash": image_hash,
            "size_bytes": len(contents),
        },
        "decision": decision,
        "identity": identity,
        "timing_ms": timing_ms,
        "status_code": 200,
        "pp2_summary": pp2_summary,
        "pp1_used": bool(question),
        "ip": None,
    }
    await db.access_logs.insert_one(access_doc)

    resp = {
        "decision": decision,
        "identity": identity,
        "candidates": candidates,
        "normativa_answer": normativa_answer,
        "timing_ms": timing_ms,
        "request_id": request_id,
    }
    return resp


@app.get("/metrics/summary")
async def metrics_summary_endpoint(
    days: int = 7,
    _=Depends(require_token),
):
    return await metrics_summary(days)


@app.get("/metrics/by-user-type")
async def metrics_by_user_type_endpoint(
    days: int = 7,
    _=Depends(require_token),
):
    return await metrics_by_user_type(days)


@app.get("/metrics/decisions")
async def metrics_decisions_endpoint(
    days: int = 7,
    _=Depends(require_token),
):
    return await metrics_decisions(days)


@app.get("/metrics/services")
async def metrics_services_endpoint(
    days: int = 7,
    _=Depends(require_token),
):
    return await metrics_services(days)


@app.get("/healthz")
async def healthz():
    """
    Health básico: estado ok + cantidad de PP2 registrados en conf/registry.yaml.
    """
    db = await get_db()

    conf_path = Path(__file__).resolve().parent.parent / "conf" / "registry.yaml"
    data = yaml.safe_load(conf_path.read_text(encoding="utf-8"))
    pp2_roster = data.get("pp2_roster", [])
    return {
        "status": "ok",
        "pp2_registered": len(pp2_roster),
    }

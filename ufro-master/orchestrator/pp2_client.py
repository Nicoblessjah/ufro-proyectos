import asyncio
import time
from typing import Any, Dict, List, Tuple
import httpx
import yaml
from pathlib import Path
from db.mongo import get_db
from datetime import datetime
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    FUSE_MARGIN: float = 0.1
    PP2_TIMEOUT_S: float = 5.0

@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_roster() -> List[Dict[str, Any]]:
    conf_path = Path(__file__).resolve().parent.parent / "conf" / "registry.yaml"
    data = yaml.safe_load(conf_path.read_text(encoding="utf-8"))
    return data.get("pp2_roster", [])

async def _call_pp2(
    client: httpx.AsyncClient,
    cfg: Dict[str, Any],
    img_bytes: bytes,
    request_id: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Ejecuta una llamada a un PP2 y devuelve:
      - resultado lógico para fusión
      - doc de logging para service_logs
    """
    t0 = time.perf_counter()
    service_name = cfg["name"]
    endpoint = cfg["endpoint_verify"]

    try:
        resp = await client.post(
            endpoint,
            files={"image": ("image.jpg", img_bytes, "image/jpeg")},
        )
        latency_ms = (time.perf_counter() - t0) * 1000.0

        doc: Dict[str, Any] = {
            "request_id": request_id,
            "ts": datetime.utcnow(),
            "service_type": "pp2",
            "service_name": service_name,
            "endpoint": endpoint,
            "latency_ms": latency_ms,
            "status_code": resp.status_code,
            "timeout": False,
        }

        result_json: Dict[str, Any] = {}
        try:
            result_json = resp.json()
            doc["result"] = result_json
        except Exception as e:
            doc["error"] = f"json error: {e}"

        score = result_json.get("score")
        threshold = cfg.get("threshold", result_json.get("threshold", 0.5))

        candidate = {
            "name": service_name,
            "score": float(score) if score is not None else None,
            "threshold": float(threshold),
        }
        return candidate, doc

    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        doc = {
            "request_id": request_id,
            "ts": datetime.utcnow(),
            "service_type": "pp2",
            "service_name": service_name,
            "endpoint": endpoint,
            "latency_ms": latency_ms,
            "status_code": None,
            "timeout": True,
            "error": str(e),
        }
        candidate = {
            "name": service_name,
            "score": None,
            "threshold": cfg.get("threshold", 0.5),
        }
        return candidate, doc

async def verify_all(
    img_bytes: bytes,
    request_id: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Llama a todos los PP2 activos en paralelo.
    Devuelve lista de candidatos y un resumen pp2_summary.
    """
    roster = [r for r in load_roster() if r.get("active", True)]
    settings = get_settings()

    timeout = settings.PP2_TIMEOUT_S
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [
            _call_pp2(client, cfg, img_bytes, request_id)
            for cfg in roster
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    candidates: List[Dict[str, Any]] = []
    logs: List[Dict[str, Any]] = []

    for cand, log_doc in results:
        candidates.append(cand)
        logs.append(log_doc)

    db = await get_db()
    if logs:
        await db.service_logs.insert_many(logs)

    timeouts = sum(1 for l in logs if l.get("timeout"))
    summary = {"queried": len(roster), "timeouts": timeouts}
    return candidates, summary

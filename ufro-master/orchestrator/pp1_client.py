from typing import Any, Dict, Optional
import httpx
from datetime import datetime
from db.mongo import get_db
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    PP1_URL: str = "http://127.0.0.1:8200/ask"

@lru_cache
def get_settings() -> Settings:
    return Settings()


async def ask_normativa(question: str, request_id: str) -> Optional[Dict[str, Any]]:
    """
    Llama a tu PP1 /ask (form-data) y loguea en service_logs.
    Devuelve dict con text + citations en formato normalizado.
    """
    settings = get_settings()
    endpoint = settings.PP1_URL

    db = await get_db()
    t0 = datetime.utcnow()

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(
                endpoint,
                data={
                    "question": question,
                    "provider": "openrouter",
                    "rag": "true",
                    "k": "4",
                    "show_sources": "true",
                },
            )
            latency_ms = (datetime.utcnow() - t0).total_seconds() * 1000.0

            log_doc = {
                "request_id": request_id,
                "ts": datetime.utcnow(),
                "service_type": "pp1",
                "service_name": "UFRO-RAG",
                "endpoint": endpoint,
                "latency_ms": latency_ms,
                "status_code": resp.status_code,
                "timeout": False,
            }

            js = {}
            try:
                js = resp.json()
                log_doc["result"] = js
            except Exception as e:
                log_doc["error"] = f"json error: {e}"

            await db.service_logs.insert_one(log_doc)

            if resp.status_code >= 400:
                return None

            answer_text = js.get("answer", "")
            citations = []
            for src in js.get("sources", []):
                citations.append(
                    {
                        "doc": src.get("title", ""),
                        "page": str(src.get("page", "")),
                        "url": src.get("url", ""),
                    }
                )

            return {
                "text": answer_text,
                "citations": citations,
            }

        except Exception as e:
            latency_ms = (datetime.utcnow() - t0).total_seconds() * 1000.0
            log_doc = {
                "request_id": request_id,
                "ts": datetime.utcnow(),
                "service_type": "pp1",
                "service_name": "UFRO-RAG",
                "endpoint": endpoint,
                "latency_ms": latency_ms,
                "status_code": None,
                "timeout": True,
                "error": str(e),
            }
            await db.service_logs.insert_one(log_doc)
            return None

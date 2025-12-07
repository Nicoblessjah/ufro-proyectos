import base64
from io import BytesIO
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

from db.mongo import get_settings

app = FastAPI(
    title="UFRO MCP Server",
    version="1.0.0",
    description="MCP-like tools: identify_person y ask_normativa",
)

class IdentifyPersonInput(BaseModel):
    image_url: Optional[str] = None
    image_b64: Optional[str] = None
    timeout_s: float = 5.0
    question: Optional[str] = None


class IdentifyPersonOutput(BaseModel):
    decision: str
    identity: Optional[dict]
    candidates: list
    timing_ms: float
    request_id: str


class AskNormativaInput(BaseModel):
    question: str


class AskNormativaOutput(BaseModel):
    text: str
    citations: list


async def _download_image(image_url: str, timeout: float) -> bytes:
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(image_url)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"No se pudo descargar la imagen (status {resp.status_code})",
            )
        return resp.content


def _decode_b64(data: str) -> bytes:
    try:
        return base64.b64decode(data)
    except Exception:
        raise HTTPException(status_code=400, detail="image_b64 inválido")


@app.post("/tools/identify_person", response_model=IdentifyPersonOutput)
async def identify_person(body: IdentifyPersonInput):
    """
    Tool MCP: dado image_url o image_b64, llama al orquestador /identify-and-answer
    y devuelve sólo la parte de identificación.
    """
    if not body.image_url and not body.image_b64:
        raise HTTPException(
            status_code=400,
            detail="Debes enviar image_url o image_b64",
        )

    settings = get_settings()
    orq_base = "http://127.0.0.1:8300"
    token = settings.api_token

    if body.image_url:
        img_bytes = await _download_image(body.image_url, body.timeout_s)
    else:
        img_bytes = _decode_b64(body.image_b64)

    files = {
        "image": ("image.jpg", img_bytes, "image/jpeg"),
    }
    data = {}
    if body.question:
        data["question"] = body.question

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-Id": "mcp-user",
        "X-User-Type": "external",
    }

    async with httpx.AsyncClient(timeout=body.timeout_s) as client:
        resp = await client.post(
            f"{orq_base}/identify-and-answer",
            files=files,
            data=data,
            headers=headers,
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Error desde orquestador: {resp.text}",
        )

    js = resp.json()
    return IdentifyPersonOutput(
        decision=js.get("decision"),
        identity=js.get("identity"),
        candidates=js.get("candidates", []),
        timing_ms=js.get("timing_ms", 0.0),
        request_id=js.get("request_id"),
    )


@app.post("/tools/ask_normativa", response_model=AskNormativaOutput)
async def ask_normativa_tool(body: AskNormativaInput):
    """
    Tool MCP: llama directamente al PP1 (/ask) usando el RAG UFRO.
    """
    settings = get_settings()
    pp1_url = settings.pp1_url

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            pp1_url,
            data={
                "question": body.question,
                "provider": "openrouter",
                "rag": "true",
                "k": "4",
                "show_sources": "true",
            },
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Error desde PP1: {resp.text}",
        )

    js = resp.json()
    answer = js.get("answer", "")
    sources = js.get("sources", [])

    citations = []
    for s in sources:
        citations.append(
            {
                "doc": s.get("title", ""),
                "page": str(s.get("page", "")),
                "url": s.get("url", ""),
            }
        )

    return AskNormativaOutput(
        text=answer,
        citations=citations,
    )

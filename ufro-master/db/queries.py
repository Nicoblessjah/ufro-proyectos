from datetime import datetime, timedelta
from typing import Any, Dict, List
from db.mongo import get_db

async def _ts_filter(days: int) -> Dict[str, Any]:
    dt = datetime.utcnow() - timedelta(days=days)
    return {"ts": {"$gte": dt}}

async def metrics_summary(days: int = 7) -> Dict[str, Any]:
    db = await get_db()
    match_stage = {"$match": await _ts_filter(days)}

    # Volumen por ruta y latencias
    pipeline = [
        match_stage,
        {
            "$group": {
                "_id": "$route",
                "count": {"$sum": 1},
                "avg_ms": {"$avg": "$timing_ms"},
            }
        },
        {"$sort": {"count": -1}},
    ]
    routes = [doc async for doc in db.access_logs.aggregate(pipeline)]

    # Errores simples
    err_pipeline = [
        match_stage,
        {
            "$group": {
                "_id": "$status_code",
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    errors = [doc async for doc in db.access_logs.aggregate(err_pipeline)]

    return {"routes": routes, "status_codes": errors}

async def metrics_by_user_type(days: int = 7) -> List[Dict[str, Any]]:
    db = await get_db()
    pipeline = [
        {"$match": await _ts_filter(days)},
        {
            "$group": {
                "_id": "$user.type",
                "requests": {"$sum": 1},
                "avg_ms": {"$avg": "$timing_ms"},
            }
        },
        {"$sort": {"requests": -1}},
    ]
    return [doc async for doc in db.access_logs.aggregate(pipeline)]

async def metrics_decisions(days: int = 7) -> List[Dict[str, Any]]:
    db = await get_db()
    pipeline = [
        {"$match": await _ts_filter(days)},
        {
            "$group": {
                "_id": "$decision",
                "total": {"$sum": 1},
            }
        },
    ]
    return [doc async for doc in db.access_logs.aggregate(pipeline)]

async def metrics_services(days: int = 7) -> List[Dict[str, Any]]:
    db = await get_db()
    dt = datetime.utcnow() - timedelta(days=days)
    pipeline = [
        {
            "$match": {
                "ts": {"$gte": dt},
            }
        },
        {
            "$group": {
                "_id": "$service_name",
                "service_type": {"$first": "$service_type"},
                "calls": {"$sum": 1},
                "avg_ms": {"$avg": "$latency_ms"},
                "timeouts": {
                    "$sum": {
                        "$cond": [{"$eq": ["$timeout", True]}, 1, 0]
                    }
                },
                "errors": {
                    "$sum": {
                        "$cond": [{"$gt": ["$status_code", 399]}, 1, 0]
                    }
                },
            }
        },
        {"$sort": {"avg_ms": -1}},
    ]
    return [doc async for doc in db.service_logs.aggregate(pipeline)]

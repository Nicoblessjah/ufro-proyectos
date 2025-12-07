import asyncio
import os
import sys

# Asegurar que la carpeta raíz del proyecto esté en sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from db.mongo import get_db

async def main():
    db = await get_db()

    await db.access_logs.create_index([("ts", -1)])
    await db.access_logs.create_index([("user.type", 1), ("ts", -1)])
    await db.access_logs.create_index([("route", 1), ("ts", -1)])
    await db.access_logs.create_index([("decision", 1), ("ts", -1)])

    await db.service_logs.create_index([("service_name", 1), ("ts", -1)])
    await db.service_logs.create_index([("service_type", 1), ("ts", -1)])
    await db.service_logs.create_index([("status_code", 1), ("ts", -1)])

    print("Índices creados correctamente.")

if __name__ == "__main__":
    asyncio.run(main())

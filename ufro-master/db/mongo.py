import motor.motor_asyncio
from pydantic_settings import BaseSettings

# -----------------------------
# SETTINGS
# -----------------------------
class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    db_name: str = "ufro_master"

    # Configuración PP1 y PP2
    pp1_url: str = "http://127.0.0.1:8200/ask"
    pp2_timeout_s: float = 5.0
    fuse_margin: float = 0.1

    # Seguridad API
    api_token: str = "supersecreto123"
    log_level: str = "info"

    class Config:
        env_file = ".env"


_settings: Settings | None = None
_client = None

# -----------------------------
# GET SETTINGS
# -----------------------------
def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# -----------------------------
# GET DATABASE
# -----------------------------
async def get_db():
    global _client
    settings = get_settings()

    if _client is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_uri)

    return _client[settings.db_name]

from typing import Any, Dict, Optional

from pydantic import BaseSettings, PostgresDsn, validator


class AsyncPostgresDsn(PostgresDsn):
    allowed_schemes = {"postgres+asyncpg", "postgresql+asyncpg"}


# For old versions of SQLAlchemy (< 1.4)
class SyncPostgresDsn(PostgresDsn):
    allowed_schemes = {"postgresql", "postgresql+psycopg2", "postgresql+pg8000"}


class Settings(BaseSettings):
    API_V2_STR: str = "/api/v2"
    PROJECT_NAME: Optional[str] = "GOAT Routing API"
    CACHE_DIR: str = "/app/src/cache"

    STREET_NETWORK_EDGE_DEFAULT_LAYER_PROJECT_ID = 36126
    STREET_NETWORK_NODE_DEFAULT_LAYER_PROJECT_ID = 37319

    NETWORK_REGION_TABLE = "basic.geofence_active_mobility"

    CATCHMENT_AREA_CAR_BUFFER_DEFAULT_SPEED = 80  # km/h
    CATCHMENT_AREA_HOLE_THRESHOLD_SQM = 10000  # 100m x 100m

    CELERY_BROKER_URL: Optional[str] = "pyamqp://guest@rabbitmq//"
    REDIS_HOST: Optional[str] = "redis"
    REDIS_PORT: Optional[str] = 6379
    REDIS_DB: Optional[str] = 0

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: Optional[str] = "5432"
    POSTGRES_DATABASE_URI: str = None

    @validator("POSTGRES_DATABASE_URI", pre=True)
    def postgres_database_uri_(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        return f'postgresql://{values.get("POSTGRES_USER")}:{values.get("POSTGRES_PASSWORD")}@{values.get("POSTGRES_SERVER")}:{values.get("POSTGRES_PORT")}/{values.get("POSTGRES_DB")}'

    ASYNC_SQLALCHEMY_DATABASE_URI: Optional[AsyncPostgresDsn] = None

    @validator("ASYNC_SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_async_db_connection(
        cls, v: Optional[str], values: Dict[str, Any]
    ) -> Any:
        if isinstance(v, str):
            return v
        return AsyncPostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    SQLALCHEMY_DATABASE_URI: Optional[SyncPostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return SyncPostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    class Config:
        case_sensitive = True


settings = Settings()

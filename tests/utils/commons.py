from datetime import datetime, timedelta
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.endpoints.v2.routing import router

TIME_BENCH = (datetime.utcnow() + timedelta(days=1)).replace(
    hour=8, minute=0, second=0, microsecond=0
).isoformat() + "Z"

app = FastAPI()
app.include_router(router)
client = TestClient(app)

logging.basicConfig(level=logging.INFO)

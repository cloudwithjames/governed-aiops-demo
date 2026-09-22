import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .db import init_db
from .config import AIOPS_AGENT_MODE
from .routers import health, demo, incidents, approvals, reports
from .i18n import I18N

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("aiops-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized at %s", os.environ.get("AIOPS_DB_PATH", "/data/aiops.db"))
    logger.info("Agent mode: %s", AIOPS_AGENT_MODE)
    yield


app = FastAPI(title="AIOps API", lifespan=lifespan)

app.include_router(health.router)
app.include_router(demo.router)
app.include_router(incidents.router)
app.include_router(approvals.router)
app.include_router(reports.router)


@app.get("/api/i18n")
async def get_i18n():
    return I18N


@app.get("/api/mode")
async def get_mode():
    return {"mode": AIOPS_AGENT_MODE}

import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Demo Backend")
START_TIME = time.time()


@app.get("/healthz")
async def healthz():
    return {"service": "demo-backend", "status": "healthy"}


@app.get("/api/status")
async def status():
    return {
        "service": "demo-backend",
        "status": "healthy",
        "version": "1.0.0",
        "message": "Customer Portal backend is healthy",
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }


@app.get("/")
async def root():
    return JSONResponse(
        status_code=200,
        content={
            "service": "demo-backend",
            "status": "healthy",
            "version": "1.0.0",
            "message": "Customer Portal backend is healthy",
        },
    )

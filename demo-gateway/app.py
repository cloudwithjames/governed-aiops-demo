import os
import time
import json
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
import httpx

app = FastAPI(title="Demo Gateway")

ADMIN_TOKEN = os.environ.get("DEMO_ADMIN_TOKEN", "replace-me")
NORMAL_BACKEND_URL = os.environ.get("NORMAL_BACKEND_URL", "http://demo-backend:8080")
FAULT_BACKEND_URL = os.environ.get("FAULT_BACKEND_URL", "http://demo-backend:8081")

backend_url = NORMAL_BACKEND_URL
change_history: list[dict] = []
error_logs: list[dict] = []
START_TIME = time.time()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _error_page(code: int, upstream: str, detail: str) -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Customer Portal - Error {code}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:"Segoe UI","Helvetica Neue","PingFang SC","Microsoft YaHei",sans-serif; background:#f0f4f8; color:#2c3e50; }}
.header {{ background:linear-gradient(135deg,#E74C3C 0%,#C0392B 100%); color:#fff; padding:24px 40px; display:flex; align-items:center; gap:16px; box-shadow:0 4px 12px rgba(231,76,60,0.3); }}
.header h1 {{ font-size:26px; font-weight:700; letter-spacing:0.5px; }}
.header .badge {{ background:rgba(0,0,0,0.25); padding:5px 14px; border-radius:20px; font-size:13px; font-weight:600; }}
.header .icon {{ font-size:28px; }}
.container {{ max-width:860px; margin:36px auto; padding:0 20px; }}
.error-card {{ background:#fff; border-radius:12px; box-shadow:0 2px 12px rgba(0,0,0,0.06); padding:28px; margin-bottom:20px; border:1px solid #e8ecf0; border-left:5px solid #E74C3C; }}
.error-card h2 {{ font-size:18px; margin-bottom:18px; color:#1a1a2e; font-weight:700; padding-left:12px; border-left:4px solid #E74C3C; }}
.error-code {{ font-size:64px; font-weight:800; color:#E74C3C; text-align:center; margin-bottom:4px; line-height:1; }}
.error-title {{ text-align:center; font-size:22px; font-weight:700; color:#E74C3C; margin-bottom:20px; }}
.error-detail {{ background:#FDEAEA; border-radius:8px; padding:16px; margin:16px 0; }}
.error-detail p {{ font-size:14px; color:#C0392B; font-weight:600; line-height:2; }}
.info-row {{ display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #f0f0f0; font-size:14px; }}
.info-row:last-child {{ border-bottom:none; }}
.info-label {{ color:#6c757d; font-weight:500; }}
.info-value {{ color:#2c3e50; font-weight:600; }}
.status-badge-err {{ display:inline-block; background:#FDEAEA; color:#E74C3C; padding:4px 12px; border-radius:20px; font-size:13px; font-weight:600; }}
.footer {{ text-align:center; padding:24px; color:#999; font-size:12px; }}
.dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; background:#E74C3C; margin-right:6px; animation:blink 1s infinite; }}
@keyframes blink {{ 0%,100%{{opacity:1;}} 50%{{opacity:0.3;}} }}
</style>
</head>
<body>
<div class="header">
    <span class="icon">&#10060;</span>
    <h1>Customer Portal</h1>
    <span class="badge"><span class="dot"></span>Offline</span>
</div>
<div class="container">
    <div class="error-card">
        <div class="error-code">{code}</div>
        <div class="error-title">Bad Gateway</div>
        <div class="error-detail">
            <p><strong>&#9888; Error:</strong> The Customer Portal is currently unavailable.</p>
            <p><strong>&#9888; Upstream:</strong> {upstream}</p>
            <p><strong>&#9888; Detail:</strong> {detail}</p>
            <p><strong>&#9888; Time:</strong> {_now()}</p>
        </div>
    </div>
    <div class="error-card">
        <h2>Diagnostic Information</h2>
        <div class="info-row"><span class="info-label">HTTP Status</span><span class="status-badge-err">{code} ERROR</span></div>
        <div class="info-row"><span class="info-label">Upstream URL</span><span class="info-value">{upstream}</span></div>
        <div class="info-row"><span class="info-label">Error Type</span><span class="info-value">Connection Refused</span></div>
    </div>
    <div class="error-card">
        <h2>What Happened?</h2>
        <div class="info-row"><span class="info-label">Cause</span><span class="info-value">Gateway cannot reach backend</span></div>
        <div class="info-row"><span class="info-label">Impact</span><span class="info-value">Customer Portal unavailable</span></div>
        <div class="info-row"><span class="info-label">Note</span><span class="info-value">Simulated incident for AI Ops demo</span></div>
    </div>
</div>
<div class="footer">Customer Portal &copy; 2026 &mdash; Powered by Huawei Cloud</div>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=code)


def _check_admin(x_demo_admin_token: str | None = Header(default=None)):
    if x_demo_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="invalid admin token")


@app.get("/healthz")
async def healthz():
    return {"service": "demo-gateway", "status": "healthy"}


@app.get("/portal")
async def portal():
    global backend_url
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{backend_url}/api/status")
            if resp.status_code == 200:
                data = resp.json()
                html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Customer Portal</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:"Segoe UI","Helvetica Neue","PingFang SC","Microsoft YaHei",sans-serif; background:#f0f4f8; color:#2c3e50; }}
.header {{ background:linear-gradient(135deg,#00B894 0%,#00896D 100%); color:#fff; padding:24px 40px; display:flex; align-items:center; gap:16px; box-shadow:0 4px 12px rgba(0,184,148,0.3); }}
.header h1 {{ font-size:26px; font-weight:700; letter-spacing:0.5px; }}
.header .badge {{ background:rgba(255,255,255,0.25); padding:5px 14px; border-radius:20px; font-size:13px; font-weight:600; }}
.header .icon {{ font-size:28px; }}
.container {{ max-width:860px; margin:36px auto; padding:0 20px; }}
.card {{ background:#fff; border-radius:12px; box-shadow:0 2px 12px rgba(0,0,0,0.06); padding:28px; margin-bottom:20px; border:1px solid #e8ecf0; }}
.card h2 {{ font-size:18px; margin-bottom:18px; color:#1a1a2e; font-weight:700; padding-left:12px; border-left:4px solid #00B894; }}
.info-row {{ display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #f0f0f0; font-size:14px; }}
.info-row:last-child {{ border-bottom:none; }}
.info-label {{ color:#6c757d; font-weight:500; }}
.info-value {{ color:#2c3e50; font-weight:600; }}
.status-ok {{ color:#00B894; font-weight:700; }}
.status-badge-ok {{ display:inline-block; background:#d4f4e2; color:#00B894; padding:4px 12px; border-radius:20px; font-size:13px; font-weight:600; }}
.hero {{ text-align:center; padding:20px 0; }}
.hero h2 {{ font-size:22px; color:#1a1a2e; border:none; padding:0; margin-bottom:8px; }}
.hero p {{ color:#6c757d; font-size:15px; }}
.footer {{ text-align:center; padding:24px; color:#999; font-size:12px; }}
.dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; background:#00B894; margin-right:6px; animation:blink 2s infinite; }}
@keyframes blink {{ 0%,100%{{opacity:1;}} 50%{{opacity:0.5;}} }}
</style>
</head>
<body>
<div class="header">
    <span class="icon">&#9989;</span>
    <h1>Customer Portal</h1>
    <span class="badge"><span class="dot"></span>Online</span>
</div>
<div class="container">
    <div class="hero">
        <h2>Welcome to Customer Portal</h2>
        <p>All systems are operating normally</p>
    </div>
    <div class="card">
        <h2>Service Status</h2>
        <div class="info-row"><span class="info-label">Service</span><span class="info-value">demo-backend</span></div>
        <div class="info-row"><span class="info-label">Status</span><span class="status-badge-ok">HEALTHY</span></div>
        <div class="info-row"><span class="info-label">Version</span><span class="info-value">{data.get("version","1.0.0")}</span></div>
        <div class="info-row"><span class="info-label">Message</span><span class="info-value">{data.get("message","Customer Portal backend is healthy")}</span></div>
    </div>
    <div class="card">
        <h2>Connection Information</h2>
        <div class="info-row"><span class="info-label">Backend URL</span><span class="info-value">{backend_url}</span></div>
        <div class="info-row"><span class="info-label">HTTP Status</span><span class="status-ok">200 OK</span></div>
        <div class="info-row"><span class="info-label">Response Time</span><span class="info-value">&lt; 50ms</span></div>
    </div>
</div>
<div class="footer">Customer Portal &copy; 2026 &mdash; Powered by Huawei Cloud</div>
</body>
</html>"""
                return HTMLResponse(content=html, status_code=200)
            else:
                return _error_page(502, backend_url, "upstream returned non-200")
    except httpx.ConnectError:
        err = {
            "level": "ERROR",
            "message": "upstream connection failed",
            "target": backend_url,
            "error": "connection refused",
            "timestamp": _now(),
        }
        error_logs.append(err)
        return _error_page(502, backend_url, "connection refused")
    except Exception as e:
        err = {
            "level": "ERROR",
            "message": "upstream connection failed",
            "target": backend_url,
            "error": str(e),
            "timestamp": _now(),
        }
        error_logs.append(err)
        return _error_page(502, backend_url, str(e))


@app.get("/api/portal/status")
async def portal_status():
    return await portal()


@app.get("/internal/config")
async def get_config(x_demo_admin_token: str | None = Header(default=None)):
    _check_admin(x_demo_admin_token)
    return {"backend_url": backend_url, "normal_url": NORMAL_BACKEND_URL, "fault_url": FAULT_BACKEND_URL}


@app.post("/internal/config/upstream")
async def set_upstream(request: Request, x_demo_admin_token: str | None = Header(default=None)):
    _check_admin(x_demo_admin_token)
    global backend_url
    body = await request.json()
    new_url = body.get("backend_url")
    if not new_url:
        raise HTTPException(status_code=400, detail="backend_url required")
    old_url = backend_url
    backend_url = new_url
    if new_url == NORMAL_BACKEND_URL:
        error_logs.clear()
    change = {
        "timestamp": _now(),
        "field": "backend_url",
        "old": old_url,
        "new": new_url,
        "source": body.get("source", "api"),
    }
    change_history.append(change)
    return {"status": "ok", "old": old_url, "new": new_url, "change": change}


@app.get("/internal/logs")
async def get_logs(x_demo_admin_token: str | None = Header(default=None)):
    _check_admin(x_demo_admin_token)
    return {"entries": error_logs[-50:]}


@app.get("/internal/changes")
async def get_changes(x_demo_admin_token: str | None = Header(default=None)):
    _check_admin(x_demo_admin_token)
    return {"changes": change_history[-50:]}


@app.post("/internal/reset")
async def reset(x_demo_admin_token: str | None = Header(default=None)):
    _check_admin(x_demo_admin_token)
    global backend_url
    old_url = backend_url
    backend_url = NORMAL_BACKEND_URL
    error_logs.clear()
    change = {
        "timestamp": _now(),
        "field": "backend_url",
        "old": old_url,
        "new": NORMAL_BACKEND_URL,
        "source": "reset",
    }
    change_history.append(change)
    return {"status": "ok", "backend_url": backend_url}


@app.post("/internal/inject-fault")
async def inject_fault(x_demo_admin_token: str | None = Header(default=None)):
    _check_admin(x_demo_admin_token)
    global backend_url
    old_url = backend_url
    backend_url = FAULT_BACKEND_URL
    change = {
        "timestamp": _now(),
        "field": "backend_url",
        "old": old_url,
        "new": FAULT_BACKEND_URL,
        "source": "demo-fault-injection",
    }
    change_history.append(change)
    return {"status": "ok", "backend_url": backend_url}

import uuid
import time
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

RATE_LIMIT_B = 14
WINDOW_SECONDS = 10
rate_limit_db = {}

# ⚠️ ULTRA-PERMISSIVE CORS SETUP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
    allow_credentials=True
)

@app.middleware("http")
async def traffic_controller(request: Request, call_next):
    # 1. CORS Preflight Handling (Crucial for "Failed to fetch" errors)
    if request.method == "OPTIONS":
        return Response(status_code=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Expose-Headers": "X-Request-ID"
        })

    # 2. Context ID Logic
    inbound_id = request.headers.get("X-Request-ID")
    request_id = inbound_id if inbound_id else str(uuid.uuid4())
    
    # 3. Rate Limiting
    client_id = request.headers.get("X-Client-Id")
    if client_id:
        now = time.time()
        history = [ts for ts in rate_limit_db.get(client_id, []) if now - ts < WINDOW_SECONDS]
        if len(history) >= RATE_LIMIT_B:
            return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})
        history.append(now)
        rate_limit_db[client_id] = history

    response = await call_next(request)
    
    # 4. Mandatory Header Echo
    response.headers["X-Request-ID"] = request_id
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"
    return response

@app.get("/ping")
@app.get("/ping/ping")
def ping(request: Request):
    return {
        "email": "24f2004755@ds.study.iitm.ac.in", 
        "request_id": request.headers.get("X-Request-ID")
    }

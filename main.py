import uuid
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

RATE_LIMIT_B = 14
WINDOW_SECONDS = 10
rate_limit_db = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

@app.middleware("http")
async def traffic_controller(request: Request, call_next):
    # 1. FORCE ID GENERATION: If missing, generate immediately
    inbound_id = request.headers.get("X-Request-ID")
    request_id = inbound_id if inbound_id else str(uuid.uuid4())
    
    # Add to request state so our functions can access it easily
    request.state.request_id = request_id
    
    # 2. Rate Limiting
    client_id = request.headers.get("X-Client-Id")
    if client_id:
        now = time.time()
        history = [ts for ts in rate_limit_db.get(client_id, []) if now - ts < WINDOW_SECONDS]
        if len(history) >= RATE_LIMIT_B:
            return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})
        history.append(now)
        rate_limit_db[client_id] = history

    response = await call_next(request)
    
    # 3. Echo the ID in the RESPONSE HEADER
    response.headers["X-Request-ID"] = request_id
    return response

# Both /ping and /ping/ping work to stop the 404s
@app.get("/ping")
@app.get("/ping/ping")
def ping(request: Request):
    return {
        "email": "24f2004755@ds.study.iitm.ac.in", 
        "request_id": request.state.request_id
    }

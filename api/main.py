import os
import re
import uuid
import shutil
import time
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from inference import detect_potholes
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL")

# Proxy arkasından gelen gerçek istemci IP adresini al
def get_real_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)

limiter = Limiter(key_func=get_real_ip)
app = FastAPI(title="Yol Hasar Tespit API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def validate_image(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Sadece PNG veya JPG formatı kabul edilir.")

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Görsel boyutu çok büyük (Max 5MB).")

def sanitize_str(val: str, max_len: int = 64) -> str:
    if not isinstance(val, str):
        return "unknown"
    cleaned = re.sub(r"[^a-zA-Z0-9_,.-]", "", val)
    return cleaned[:max_len] if cleaned else "unknown"

@app.post("/predict")
@limiter.limit("10/minute")
async def predict(request: Request, file: UploadFile = File(...), x_session_id: str = Header(None)):
    validate_image(file)

    os.makedirs("temp_images", exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex}.jpg"
    file_path = os.path.join("temp_images", safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        results = detect_potholes(file_path)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    return {"kullanici": "Vatandas", "detections": results}

@app.post("/report")
@limiter.limit("5/minute")
async def report(request: Request):
    data = await request.json()
    session_id = sanitize_str(data.get("session_id", "unknown"), 32)
    location = sanitize_str(data.get("location", "unknown"), 64)

    with open("app_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{time.ctime()} | RAPORLANDI | User: Vatandas | Session: {session_id} | Loc: {location}\n")

    return {"status": "success", "message": "Rapor başarıyla alındı."}

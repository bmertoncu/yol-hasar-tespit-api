import os
import shutil
import time
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from inference import detect_potholes
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# --- AYARLAR ---
load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL")

# Hız sınırlayıcı (Dakikada en fazla 10 analiz)
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DOSYA VE GÜVENLİK KONTROLÜ ---
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB sınır

def validate_image(file: UploadFile):
    # Uzantı kontrolü
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Sadece PNG veya JPG formatı kabul edilir.")
    # Boyut kontrolü
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Görsel boyutu çok büyük (Max 5MB).")

# --- ENDPOINTLER ---

@app.post("/predict")
@limiter.limit("10/minute") # Kötü amaçlı seri istekleri engeller
async def predict(request: Request, file: UploadFile = File(...), x_session_id: str = Header(None)):
    validate_image(file) # İçerik filtresi
    
    session_id = x_session_id if x_session_id else "unknown"
    os.makedirs("temp_images", exist_ok=True) 
    file_path = os.path.join("temp_images", f"{session_id}.jpg")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        results = detect_potholes(file_path)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            
    return {"kullanici": "Vatandas", "detections": results}

@app.post("/report")
@limiter.limit("5/minute") # Rapor spam'ini engeller
async def report(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "unknown")
    location = data.get("location", "unknown")
    
    with open("app_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{time.ctime()} | RAPORLANDI | User: Vatandas | Session: {session_id} | Loc: {location}\n")
        
    return {"status": "success", "message": "Rapor başarıyla alındı."}
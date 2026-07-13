from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import time
from inference import detect_potholes
from dotenv import load_dotenv

# .env dosyasını hafızaya yükle
load_dotenv()

# .env içindeki FRONTEND_URL değerini çek (Eğer bulamazsa varsayılan olarak "*" yap)
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

app = FastAPI()

# CORS Ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],  # Tırnak işaretlerini KALDIRDIK ve değişkeni verdik
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Endpoint: Görüntü Analizi
@app.post("/predict")
async def predict(file: UploadFile = File(...), x_session_id: str = Header(None)):
    try:
        # Header'dan gelen veriyi kullanıyoruz, yoksa 'unknown' atıyoruz
        session_id = x_session_id if x_session_id else "unknown"
        
        os.makedirs("temp_images", exist_ok=True) 
        file_path = os.path.join("temp_images", f"{session_id}.jpg")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        results = detect_potholes(file_path)
        return {"detections": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Endpoint: Raporlama
@app.post("/report")
async def report(request: Request):
    try:
        data = await request.json()
        session_id = data.get("session_id", "unknown")
        location = data.get("location", "unknown")
        
        # Verileri yerel bir metin dosyasına logla
        with open("app_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()} | RAPORLANDI | Session: {session_id} | Loc: {location}\n")
            
        return {"status": "success", "message": "Rapor basariyla alindi."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
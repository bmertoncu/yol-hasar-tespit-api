from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import time
from inference import detect_potholes 

app = FastAPI()

# CORS Ayarları (Dokunma)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Endpoint: Görüntü Analizi
@app.post("/predict")
async def predict(request: Request, file: UploadFile = File(...)):
    try:
        session_id = request.headers.get("X-Session-ID", "unknown")
        os.makedirs("temp_images", exist_ok=True)
        file_path = os.path.join("temp_images", f"{session_id}.jpg")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        results = detect_potholes(file_path)
        return {"detections": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Endpoint: Raporlama (404 Hatasını Çözen Kısım)
@app.post("/report")
async def report(request: Request):
    try:
        data = await request.json()
        session_id = data.get("session_id", "unknown")
        location = data.get("location", "unknown")
        
        # Log dosyasına yaz
        with open("app_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()} | RAPORLANDI | Session: {session_id} | Loc: {location}\n")
            
        return {"status": "success", "message": "Rapor basariyla alindi."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
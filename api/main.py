from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import shutil
import os
import time
from datetime import datetime, timedelta
import jwt

#YOLO model importu
from inference import detect_potholes 

# --- JWT GÜVENLİK AYARLARI ---
SECRET_KEY = "adana_bb_gizli_anahtar"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- SWAGGER UI DOKÜMANTASYON BİLGİLERİ ---
app = FastAPI(
    title="Yol ve Çukur Tespit Sistemi API",
    description="Vatandaş raporlama ve saha araçları görüntü analizi uç noktaları.",
    version="1.0.0"
)

# CORS: Frontend ve Backend'in farklı portlarda konuşabilmesi için izin tanımları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- JWT YARDIMCI FONKSİYONLARI ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Geçersiz kimlik doğrulama")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token süresi dolmuş")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz token")

# --- KİMLİK DOĞRULAMA ENDPOINT'İ ---
@app.post("/token", tags=["Güvenlik ve Yetkilendirme"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Prototip için basit kontrol
    if form_data.username == "saha_araci" and form_data.password == "adana123":
        access_token = create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Hatalı kullanıcı adı veya şifre")

# --- 1. ENDPOINT: GÖRÜNTÜ ANALİZİ (Senin Kodun + Güvenlik) ---
@app.post("/predict", tags=["Otonom Tespit Modülü"])
async def predict(file: UploadFile = File(...), x_session_id: str = Header(None), current_user: str = Depends(verify_token)):
    try:
        # Header'dan gelen veriyi kullanıyoruz, yoksa 'unknown' atıyoruz
        session_id = x_session_id if x_session_id else "unknown"
        
        os.makedirs("temp_images", exist_ok=True) 
        file_path = os.path.join("temp_images", f"{session_id}.jpg")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # YOLO modeline gönderim
        results = detect_potholes(file_path)
        return {"kullanici": current_user, "detections": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 2. ENDPOINT: RAPORLAMA (Senin Kodun + Güvenlik) ---
@app.post("/report", tags=["Vatandaş Bildirim Modülü"])
async def report(request: Request, current_user: str = Depends(verify_token)):
    try:
        data = await request.json()
        session_id = data.get("session_id", "unknown")
        location = data.get("location", "unknown")
        
        # Verileri yerel bir metin dosyasına logla
        with open("app_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()} | RAPORLANDI | User: {current_user} | Session: {session_id} | Loc: {location}\n")
            
        return {"status": "success", "message": "Rapor başarıyla alındı."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
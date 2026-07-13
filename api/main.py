import os
import shutil
import time
from datetime import datetime, timedelta
import jwt
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from pydantic import BaseModel
from inference import detect_potholes 

# --- ORTAM DEĞİŞKENLERİ VE AYARLAR ---
load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
SECRET_KEY = os.getenv("SECRET_KEY", "gizli_anahtar_yoksa_bunu_kullan")
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

# Admin bilgilerini .env dosyasından çekiyoruz (bulamazsa varsayılan olarak admin/adana123 kullanır)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "adana123")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Canlı ortamda Swagger'ı kapatıyoruz
app = FastAPI(
    title="Yol ve Çukur Tespit Sistemi API",
    docs_url=None if ENVIRONMENT == "production" else "/docs",
    redoc_url=None if ENVIRONMENT == "production" else "/redoc",
)

# CORS Ayarları: Çalışan güncel ayarlarına dokunmuyoruz
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GEÇİCİ VERİTABANI VE MODEL (TEST İÇİN) ---
# Kullanıcı adı ve şifre artık .env üzerinden belirleniyor
fake_users_db = {
    ADMIN_USERNAME: ADMIN_PASSWORD
}

class UserCreate(BaseModel):
    username: str
    password: str

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

# --- YENİ KULLANICI OLUŞTURMA ENDPOINT'İ ---
@app.post("/register", tags=["Güvenlik ve Yetkilendirme"])
async def register_test_user(user: UserCreate):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten alınmış.")
    
    # Yeni kullanıcıyı sözlüğe ekle
    fake_users_db[user.username] = user.password
    return {
        "durum": "başarılı", 
        "mesaj": f"Kullanıcı '{user.username}' başarıyla oluşturuldu."
    }

# --- KİMLİK DOĞRULAMA ENDPOINT'İ ---
@app.post("/token", tags=["Güvenlik ve Yetkilendirme"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Gönderilen kullanıcı adı sözlükte var mı ve şifresi eşleşiyor mu kontrol et
    if form_data.username in fake_users_db and fake_users_db[form_data.username] == form_data.password:
        access_token = create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(status_code=400, detail="Hatalı kullanıcı adı veya şifre")

# --- 1. ENDPOINT: GÖRÜNTÜ ANALİZİ ---
@app.post("/predict", tags=["Otonom Tespit Modülü"])
async def predict(file: UploadFile = File(...), x_session_id: str = Header(None), current_user: str = Depends(verify_token)):
    try:
        session_id = x_session_id if x_session_id else "unknown"
        os.makedirs("temp_images", exist_ok=True) 
        file_path = os.path.join("temp_images", f"{session_id}.jpg")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        results = detect_potholes(file_path)
        
        # İşlem bitince geçici dosyayı temizle (Sunucu şişmesin)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {"kullanici": current_user, "detections": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 2. ENDPOINT: RAPORLAMA ---
@app.post("/report", tags=["Vatandaş Bildirim Modülü"])
async def report(request: Request, current_user: str = Depends(verify_token)):
    try:
        data = await request.json()
        session_id = data.get("session_id", "unknown")
        location = data.get("location", "unknown")
        
        with open("app_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()} | RAPORLANDI | User: {current_user} | Session: {session_id} | Loc: {location}\n")
            
        return {"status": "success", "message": "Rapor başarıyla alındı."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
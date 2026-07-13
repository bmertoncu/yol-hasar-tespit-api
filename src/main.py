import os
import time
import jwt
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

from src.config import settings
from src.detector import detector
from src.gps_resolver import get_live_location
from src.utils import annotate_and_save, log_incident, is_duplicate_pothole

# .env yükle
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "varsayilan_cok_gizli_anahtar")
ALGORITHM = "HS256"

app = FastAPI(title=os.getenv("PROJECT_NAME", "Arac Takip Sistemi"))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- GÜVENLİK KATMANI ---
async def verify_vehicle_jwt(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        vehicle_id: str = payload.get("sub")
        if not vehicle_id:
            raise HTTPException(status_code=401, detail="Geçersiz araç kimliği.")
        return vehicle_id
    except Exception:
        raise HTTPException(status_code=401, detail="Token doğrulaması başarısız.")

# --- ENDPOINT ---
@app.post("/api/v1/vehicle/stream")
async def receive_camera_stream(
    file: UploadFile = File(...),
    vehicle_id: str = Depends(verify_vehicle_jwt) # Artık güvenli
):
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    timestamp = int(time.time() * 1000)
    file_path = os.path.join(settings.TEMP_DIR, f"{vehicle_id}_{timestamp}.jpg")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        has_pothole, detections = detector.analyze_frame(file_path)
        gps_data = {}
        is_saved = False

        if has_pothole:
            gps_data = get_live_location(vehicle_id)
            if not is_duplicate_pothole(gps_data):
                saved_image_path = annotate_and_save(file_path, detections)
                if saved_image_path:
                    log_incident(vehicle_id, gps_data, saved_image_path)
                    is_saved = True

        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "pothole_detected": has_pothole,
            "vehicle_id": vehicle_id,
            "resolved_location": gps_data,
            "is_new_incident_saved": is_saved
        }

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))
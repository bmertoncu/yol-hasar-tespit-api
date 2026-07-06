from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends
from fastapi.responses import FileResponse
import shutil
import os
import time

from src.config import settings
from src.detector import detector
from src.gps_resolver import get_live_location
# Yeni yazdığımız utils fonksiyonlarını projeye dahil ediyoruz
from src.utils import annotate_and_save, log_incident, is_duplicate_pothole

app = FastAPI(title=settings.PROJECT_NAME)

async def verify_vehicle_token(x_auth_token: str = Header(None)):
    if x_auth_token != settings.API_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Yetkisiz Erişim.")
    return x_auth_token

@app.post("/api/v1/vehicle/stream", dependencies=[Depends(verify_vehicle_token)])
async def receive_camera_stream(
    file: UploadFile = File(...),
    x_vehicle_id: str = Header(None)
):
    if not x_vehicle_id:
        raise HTTPException(status_code=400, detail="Eksik Parametre.")

    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    timestamp = int(time.time() * 1000)
    file_path = os.path.join(settings.TEMP_DIR, f"{x_vehicle_id}_{timestamp}.jpg")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        has_pothole, detections = detector.analyze_frame(file_path)
        gps_data = {}
        is_saved = False

        if has_pothole:
            gps_data = get_live_location(x_vehicle_id)
            
            # Kopya kontrolü: Aynı konumda yakın zamanda çukur bulunmadıysa işle
            if not is_duplicate_pothole(gps_data):
                # Çukuru çiz ve kaydet
                saved_image_path = annotate_and_save(file_path, detections)
                if saved_image_path:
                    # Log dosyasına yaz
                    log_incident(x_vehicle_id, gps_data, saved_image_path)
                    is_saved = True
            else:
                # Sunucuyu yormamak için işlemi pas geçiyoruz
                pass

        # Temizlik: Orijinal işlenmemiş gelen resmi siliyoruz
        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "pothole_detected": has_pothole,
            "count": len(detections),
            "resolved_location": gps_data,
            "is_new_incident_saved": is_saved # İstemciye resmin kaydedilip kaydedilmediğini bildir
        }

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))
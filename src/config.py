import os

class Settings:
    # Proje İsmi
    PROJECT_NAME: str = "Belediye Araçları Canlı Yol Hasar Tespit Sistemi"
    # Yolo Model Yolu
    MODEL_PATH: str = os.getenv("MODEL_PATH", "models/best.pt")
    # Güven Eşiği (0,70 veya 0,71 en iyisi)
    CONFIDENCE_THRESHOLD: float = 0.70
    # Geçici dosya yolu
    TEMP_DIR: str = "stream_temp"
    # Log yolu
    LOG_FILE: str = "pothole_incidents.log"
    
    # Güvenlik katmanı: Araçların sunucuya yetkisiz veri atmasını engellemek için
    API_AUTH_TOKEN: str = os.getenv("VEHICLE_API_TOKEN", "adana_belediyesi_secret_token")

settings = Settings()
import os

class Settings:
    PROJECT_NAME: str = "Belediye Araçları Canlı Yol Hasar Tespit Sistemi"
    MODEL_PATH: str = os.getenv("MODEL_PATH", "models/best.pt")
    CONFIDENCE_THRESHOLD: float = 0.70
    TEMP_DIR: str = "stream_temp"
    LOG_FILE: str = "pothole_incidents.log"
    
    # Güvenlik katmanı: Araçların sunucuya yetkisiz veri atmasını engellemek için
    API_AUTH_TOKEN: str = os.getenv("VEHICLE_API_TOKEN", "adana_belediyesi_secret_token")

settings = Settings()
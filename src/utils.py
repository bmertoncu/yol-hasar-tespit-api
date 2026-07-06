import cv2
import logging
import os
import math
import time
from datetime import datetime

# ==========================================
# 1. LOGLAMA AYARLARI
# ==========================================
logging.basicConfig(
    filename='pothole_incidents.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# ==========================================
# 2. GÖRSEL İŞLEME VE DOSYALAMA
# ==========================================
def annotate_and_save(image_path, detections, output_dir="incidents"):
    """Görseli okur, çukurları kırmızı kutuyla çizer ve kaydeder."""
    os.makedirs(output_dir, exist_ok=True)
    
    img = cv2.imread(image_path)
    if img is None:
        return None

    for det in detections:
        x1, y1, x2, y2 = map(int, det['bbox'])
        # Kutuyu çiz (Kırmızı renk)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)
        # Etiketi yaz
        cv2.putText(img, f"Cukur: {det['confidence']:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(output_dir, f"pothole_{timestamp}.jpg")
    cv2.imwrite(save_path, img)
    return save_path

def log_incident(vehicle_id, gps_data, image_path):
    """Olayı log dosyasına kaydeder."""
    log_message = f"ARAC: {vehicle_id} | KONUM: {gps_data} | FOTO: {image_path}"
    logging.info(log_message)

# ==========================================
# 3. MESAFE FİLTRESİ (MÜKERRER KAYIT ÖNLEME)
# ==========================================
RECENT_POTHOLES = []
COOLDOWN_SECONDS = 300  # 5 dakika
DISTANCE_THRESHOLD_METERS = 15  # 15 metre çap

def haversine_distance(lat1, lon1, lat2, lon2):
    """İki GPS koordinatı (enlem, boylam) arasındaki mesafeyi metre cinsinden hesaplar."""
    R = 6371000  # Dünya yarıçapı (metre)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def is_duplicate_pothole(gps_data):
    """
    Yeni gelen konumun 15 metre yakınlarında son 5 dakika 
    içinde çukur kaydedilip edilmediğini kontrol eder.
    """
    global RECENT_POTHOLES
    current_time = time.time()
    
    # Süresi dolmuş eski kayıtları bellekten temizle
    RECENT_POTHOLES = [p for p in RECENT_POTHOLES if current_time - p[2] < COOLDOWN_SECONDS]

    if not isinstance(gps_data, dict) or "lat" not in gps_data or "lon" not in gps_data:
        return False 

    new_lat = float(gps_data["latitude"])
    new_lon = float(gps_data["longitude"])

    for lat, lon, timestamp in RECENT_POTHOLES:
        distance = haversine_distance(new_lat, new_lon, lat, lon)
        if distance < DISTANCE_THRESHOLD_METERS:
            return True  # Kopya tespit edildi!

    # Kopya değilse yeni çukuru listeye ekle
    RECENT_POTHOLES.append((new_lat, new_lon, current_time))
    return False
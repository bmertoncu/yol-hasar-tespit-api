import cv2
import logging
import os
import math
import time
from datetime import datetime

logging.basicConfig(
    filename='pothole_incidents.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def annotate_and_save(image_path, detections, output_dir="incidents"):
    """Tespit edilen çukurları görsel üzerinde işaretleyip kaydeder."""
    os.makedirs(output_dir, exist_ok=True)

    img = cv2.imread(image_path)
    if img is None:
        return None

    for det in detections:
        x1, y1, x2, y2 = map(int, det['bbox'])
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)
        cv2.putText(img, f"Cukur: {det['confidence']:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(output_dir, f"pothole_{timestamp}.jpg")
    cv2.imwrite(save_path, img)
    return save_path

def log_incident(vehicle_id, gps_data, image_path):
    log_message = f"ARAC: {vehicle_id} | KONUM: {gps_data} | FOTO: {image_path}"
    logging.info(log_message)

# Coğrafi mükerrer kayıt filtreleme parametreleri
RECENT_POTHOLES = []
COOLDOWN_SECONDS = 300
DISTANCE_THRESHOLD_METERS = 15

def haversine_distance(lat1, lon1, lat2, lon2):
    """İki GPS koordinatı arasındaki mesafeyi metre cinsinden hesaplar."""
    R = 6371000
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
    """Son 5 dakika içinde 15 metre yakınlıkta kayıtlı çukur olup olmadığını denetler."""
    global RECENT_POTHOLES
    current_time = time.time()

    RECENT_POTHOLES = [p for p in RECENT_POTHOLES if current_time - p[2] < COOLDOWN_SECONDS]

    if not isinstance(gps_data, dict) or "latitude" not in gps_data or "longitude" not in gps_data:
        return False

    if gps_data["latitude"] is None or gps_data["longitude"] is None:
        return False

    new_lat = float(gps_data["latitude"])
    new_lon = float(gps_data["longitude"])

    for lat, lon, timestamp in RECENT_POTHOLES:
        distance = haversine_distance(new_lat, new_lon, lat, lon)
        if distance < DISTANCE_THRESHOLD_METERS:
            return True

    RECENT_POTHOLES.append((new_lat, new_lon, current_time))
    return False

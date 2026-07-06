import os
import threading
import time
from queue import Queue
import cv2
import requests

# ==========================================
# YAPILANDIRMA (CONFIG)
# ==========================================
API_URL = "http://127.0.0.1:8000/api/v1/vehicle/stream"
VEHICLE_ID = "TEST_MACBOOK_AIR"
AUTH_TOKEN = "adana_belediyesi_secret_token"

FPS_TARGET = 30
FRAME_DELAY = 1.0 / FPS_TARGET
TARGET_SIZE = (640, 640)

# Video işlenirken kare kaçırmamak ama belleği de şişirmemek için kuyruk sınırı
request_queue = Queue(maxsize=5)


# ==========================================
# ARKA PLAN AĞ İŞÇİSİ (WORKER)
# ==========================================
def network_worker():
    """Arka planda kuyruğa gelen video karelerini API'ye gönderir."""
    headers = {"X-Vehicle-ID": VEHICLE_ID, "x-auth-token": AUTH_TOKEN}

    while True:
        img_encoded = request_queue.get()
        if img_encoded is None:
            break  # Çıkış sinyali

        files = {"file": ("test_frame.jpg", img_encoded.tobytes(), "image/jpeg")}

        try:
            response = requests.post(
                API_URL, files=files, headers=headers, timeout=1
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("pothole_detected"):
                    print(
                        f"[!] ÇUKUR TESPİT EDİLDİ! Konum: {result['resolved_location']}"
                    )
        except requests.exceptions.RequestException:
            pass  # Bağlantı hataları akışı bozmasın diye loglanmaz

        request_queue.task_done()


# ==========================================
# ANA VİDEO DÖNGÜSÜ
# ==========================================
def start_video_stream():
    # Video dosyasının tam yolunu bulma
    current_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(current_dir, "video.mp4")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Hata: Video dosyasına erişilemedi: {video_path}")
        return

    # Arka plan işçisini başlat
    worker_thread = threading.Thread(target=network_worker, daemon=True)
    worker_thread.start()

    print("Video akışı başlatıldı. 30 FPS simülasyonu ve Arka Plan Analizi aktif...")
    prev_time = 0

    try:
        while True:
            # Gerçek zamanlı video oynatma simülasyonu (30 FPS)
            time_elapsed = time.time() - prev_time
            if time_elapsed < FRAME_DELAY:
                time.sleep(FRAME_DELAY - time_elapsed)

            prev_time = time.time()

            ret, frame = cap.read()
            if not ret:
                print("\nVideo başarıyla sona erdi.")
                break

            # Görüntüyü işle ve göster
            resized_frame = cv2.resize(
                frame, TARGET_SIZE, interpolation=cv2.INTER_AREA
            )
            cv2.imshow("Video Test Yayini - 30 FPS", resized_frame)

            # JPEG formatına sıkıştırma
            _, img_encoded = cv2.imencode(".jpg", resized_frame)

            # Kuyruk durumuna göre kareyi gönder
            if not request_queue.full():
                request_queue.put_nowait(img_encoded)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nVideo testi kullanıcı tarafından sonlandırıldı.")
    finally:
        request_queue.put(None)  # Worker thread'i kapat
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    start_video_stream()
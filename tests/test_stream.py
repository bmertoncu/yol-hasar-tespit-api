import threading
import time
from queue import Queue
import cv2
import requests

API_URL = "http://127.0.0.1:8000/api/v1/vehicle/stream"
VEHICLE_ID = "TEST_MACBOOK_AIR"
AUTH_TOKEN = "adana_belediyesi_secret_token"

FPS_TARGET = 30
FRAME_DELAY = 1.0 / FPS_TARGET
TARGET_SIZE = (640, 640)

request_queue = Queue(maxsize=5)


def network_worker():
    """Kuyruktaki kareleri arka planda API servisine iletir."""
    headers = {"X-Vehicle-ID": VEHICLE_ID, "x-auth-token": AUTH_TOKEN}

    while True:
        img_encoded = request_queue.get()
        if img_encoded is None:
            break

        files = {"file": ("test_frame.jpg", img_encoded.tobytes(), "image/jpeg")}

        try:
            response = requests.post(
                API_URL, files=files, headers=headers, timeout=1
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("pothole_detected"):
                    print(f"[!] Çukur tespit edildi - Konum: {result['resolved_location']}")
        except requests.exceptions.RequestException:
            pass

        request_queue.task_done()


def start_camera_stream():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Hata: Kameraya erişilemedi.")
        return

    worker_thread = threading.Thread(target=network_worker, daemon=True)
    worker_thread.start()

    print("Kamera akışı başlatıldı (30 FPS)...")
    prev_time = 0

    try:
        while True:
            time_elapsed = time.time() - prev_time
            if time_elapsed < FRAME_DELAY:
                time.sleep(FRAME_DELAY - time_elapsed)

            prev_time = time.time()

            ret, frame = cap.read()
            if not ret:
                continue

            resized_frame = cv2.resize(frame, TARGET_SIZE, interpolation=cv2.INTER_AREA)
            cv2.imshow("Kamera Akisi - 30 FPS", resized_frame)

            _, img_encoded = cv2.imencode(".jpg", resized_frame)

            if not request_queue.full():
                request_queue.put_nowait(img_encoded)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nKamera testi sonlandırıldı.")
    finally:
        request_queue.put(None)
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    start_camera_stream()

import cv2
import requests
import time

# Yapılandırma
API_URL = "http://127.0.0.1:8000/api/v1/vehicle/stream"
VEHICLE_ID = "TEST_MACBOOK_AIR"
AUTH_TOKEN = "adana_belediyesi_secret_token"  # config.py'deki token ile aynı olmalı

def start_test_stream():
    # Süreklilik Kamerası genellikle varsayılan (0) veya ikincil (1) indeksle gelir.
    # Eğer FaceTime kamerası açılırsa, indeksi 1 veya 2 olarak değiştirebilirsin.
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Hata: Süreklilik Kamerasına erişilemedi.")
        return

    print("Süreklilik Kamerası aktif. Analiz için sunucuya veri gönderiliyor... (Durdurmak için CTRL+C)")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            # Canlı önizleme penceresi aç (Kameranın ne gördüğünü canlı izle)
            cv2.imshow("Sureklilik Kamerasi - Arac Testi", frame)

            # Görseli JPEG olarak sıkıştır
            _, img_encoded = cv2.imencode('.jpg', frame)
            
            files = {
                'file': ('test_frame.jpg', img_encoded.tobytes(), 'image/jpeg')
            }
            headers = {
                'X-Vehicle-ID': VEHICLE_ID,
                'x-auth-token': AUTH_TOKEN
            }

            try:
                # Sunucuya gönder
                response = requests.post(API_URL, files=files, headers=headers, timeout=1)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("pothole_detected"):
                        print(f"[!] ÇUKUR TESPİT EDİLDİ! Eşleşen Konum: {result['resolved_location']}")
                else:
                    print(f"Sunucu Hatası: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException:
                print("Sunucuya bağlanılamadı...")

            # OpenCV penceresinin açık kalması ve q tuşuna basınca kapanması için
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Saniyede 2 kare gönderecek şekilde bekle (0.5 saniye)
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nTest sonlandırıldı.")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    start_test_stream()
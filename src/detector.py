from ultralytics import YOLO
import os
from src.config import settings

class PotholeDetector:
    def __init__(self):
        # Hiçbir ayarı zorlamadan modeli en saf haliyle yüklüyoruz
        if os.path.exists(settings.MODEL_PATH):
            self.model = YOLO(settings.MODEL_PATH)
        else:
            self.model = YOLO("yolov8n-seg.pt")

    def analyze_frame(self, image_path: str):
        pothole_detected = False
        detections = []
        
        try:
            # Modeli doğrudan çalıştır ve sonuçları al
            results = self.model(image_path, verbose=False)
            
            for r in results:
                # Algılanan nesne varsa kutu koordinatlarını topla
                if r.boxes is not None:
                    for box in r.boxes:
                        conf = float(box.conf)
                        if conf >= settings.CONFIDENCE_THRESHOLD:
                            pothole_detected = True
                            detections.append({
                                "confidence": conf,
                                "bbox": box.xyxy.tolist()[0]
                            })
                            
        except Exception as e:
            print(f"[-] Hata: {str(e)}")
            
        return pothole_detected, detections

detector = PotholeDetector()
import os
from ultralytics import YOLO
from src.config import settings


class PotholeDetector:

    def __init__(self):
        """Çukur tespit modelini yükler ve mükerrer engelleme hafızasını
        başlatır.
        """
        # Model Yükleme
        if os.path.exists(settings.MODEL_PATH):
            self.model = YOLO(settings.MODEL_PATH)
        else:
            self.model = YOLO("yolov8n-seg.pt")

        # Mükerrer (Aynı) Çukurları Engelleme Ayarları
        self.last_detected_boxes = []  # Bir önceki karedeki çukurların hafızası
        self.iou_threshold = 0.4  # %40 ve üzeri örtüşme aynı çukur sayılır (çok çalışmıyor gibi kontrol etmek lazım)

    def _calculate_iou(self, box1, box2):
        """İki kutu (bounding box) arasındaki Kesişim / Birleşim (IoU) oranını
        hesaplar.
        """
        # Koordinatları ayrıştır: [xmin, ymin, xmax, ymax]
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        # 1. Kesişim (Intersection) alanının sınırlarını bul
        x_left = max(x1_1, x1_2)
        y_top = max(y1_1, y1_2)
        x_right = min(x2_1, x2_2)
        y_bottom = min(y2_1, y2_2)

        # Eğer kutular hiç çakışmıyorsa IoU 0'dır
        if x_right < x_left or y_bottom < y_top:
            return 0.0

        # 2. Alanları hesapla
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)

        # 3. Birleşim (Union) alanını hesapla
        union_area = box1_area + box2_area - intersection_area

        if union_area == 0:
            return 0.0

        return intersection_area / union_area

    def analyze_frame(self, image_path: str):
        """Gelen kareyi YOLO ile analiz eder, yeni çukurları eski
        karelerdekilerle kıyaslayarak tespit eder.
        """
        pothole_detected = False
        detections = []
        current_frame_boxes = []

        try:
            # Yapay zeka modelini çalıştır (Konsol çıktısı vermemesi için verbose=False)
            results = self.model(image_path, verbose=False)

            for r in results:
                if r.boxes is None:
                    continue

                for box in r.boxes:
                    conf = float(box.conf)

                    # Güven eşiğinin (Confidence) altındaki tahminleri ele
                    if conf < settings.CONFIDENCE_THRESHOLD:
                        continue

                    # Tespit edilen çukurun koordinatlarını al
                    bbox = box.xyxy.tolist()[0]
                    current_frame_boxes.append(bbox)

                    # MÜKERRER KONTROLÜ: Bu çukur bir önceki karede zaten var mıydı?
                    is_duplicate = False
                    for last_bbox in self.last_detected_boxes:
                        iou = self._calculate_iou(bbox, last_bbox)

                        if iou > self.iou_threshold:
                            is_duplicate = True
                            break  # Hafızadaki bir çukurla eşleşti, aramayı kes

                    # Eğer bu yepyeni bir çukursa listeye ekle ve bayrağı kaldır
                    if not is_duplicate:
                        pothole_detected = True
                        detections.append({"confidence": conf, "bbox": bbox})

        except Exception as e:
            print(f"[-] Model Analiz Hatası: {str(e)}")

        # Mevcut karedeki tüm kutuları, bir sonraki kareye referans olması için hafızaya al
        self.last_detected_boxes = current_frame_boxes

        return pothole_detected, detections


# Global nesne tanımı
detector = PotholeDetector()
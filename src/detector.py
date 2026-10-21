import os
from ultralytics import YOLO
from src.config import settings


class PotholeDetector:

    def __init__(self):
        if os.path.exists(settings.MODEL_PATH):
            self.model = YOLO(settings.MODEL_PATH)
        else:
            self.model = YOLO("yolov8n-seg.pt")

        # Ardışık karelerde aynı çukuru tekrar kaydetmemek için önceki kare kutuları tutulur
        self.last_detected_boxes = []
        self.iou_threshold = 0.4

    def _calculate_iou(self, box1, box2):
        """İki bounding box arasındaki Kesişim / Birleşim (IoU) oranını hesaplar."""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        x_left = max(x1_1, x1_2)
        y_top = max(y1_1, y1_2)
        x_right = min(x2_1, x2_2)
        y_bottom = min(y2_1, y2_2)

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = box1_area + box2_area - intersection_area

        if union_area == 0:
            return 0.0

        return intersection_area / union_area

    def analyze_frame(self, image_path: str):
        """Kareyi YOLO ile analiz eder ve önceki kareyle IoU karşılaştırması yapar."""
        pothole_detected = False
        detections = []
        current_frame_boxes = []

        try:
            results = self.model(image_path, verbose=False)

            for r in results:
                if r.boxes is None:
                    continue

                for box in r.boxes:
                    conf = float(box.conf)
                    if conf < settings.CONFIDENCE_THRESHOLD:
                        continue

                    bbox = box.xyxy.tolist()[0]
                    current_frame_boxes.append(bbox)

                    is_duplicate = False
                    for last_bbox in self.last_detected_boxes:
                        if self._calculate_iou(bbox, last_bbox) > self.iou_threshold:
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        pothole_detected = True
                        detections.append({"confidence": conf, "bbox": bbox})

        except Exception as e:
            print(f"Model analiz hatası: {str(e)}")

        self.last_detected_boxes = current_frame_boxes
        return pothole_detected, detections


detector = PotholeDetector()

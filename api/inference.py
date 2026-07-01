from ultralytics import YOLO

# Modeli bir kere yükleyelim (M2 Mac üzerinde MPS ile çalışması için otomatik optimize eder)
model = YOLO("models/best.pt")

def detect_potholes(image_path):
    # Tahminleme yap
    results = model(image_path)
    
    # YOLO sonuçlarından tespit edilen nesnelerin bilgilerini al
    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                "class": model.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy.tolist()
            })
    return detections
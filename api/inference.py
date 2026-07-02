from ultralytics import YOLO

# Modelin hafızaya yüklenmesi
model = YOLO("models/best.pt")

def detect_potholes(image_path):
    # Modelin görsel üzerinde çıkarım yapması (Inference)
    results = model(image_path)
    
    # Tespit edilen nesnelerin sınıfını, güven skorunu ve kutu koordinatlarını çıkar
    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                "class": model.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy.tolist()
            })
    return detections
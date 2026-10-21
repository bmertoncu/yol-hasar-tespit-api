from ultralytics import YOLO

model = YOLO("models/best.pt")

def detect_potholes(image_path):
    results = model(image_path)

    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                "class": model.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy.tolist()
            })
    return detections

# vision/detection/product_detector.py

from ultralytics import YOLO
import cv2


class ProductDetector:
    def __init__(self, model_path="yolov8n.pt", confidence=0.4):
        """
        Initialize YOLO model for product detection
        """
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame):
        """
        Run detection on a frame

        Returns:
            List of detections:
            [
                {
                    "bbox": [x1, y1, x2, y2],
                    "confidence": float,
                    "class_id": int,
                    "label": str
                }
            ]
        """
        results = self.model(frame)

        detections = []

        for result in results:
            boxes = result.boxes

            for box in boxes:
                conf = float(box.conf[0])
                if conf < self.confidence:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                class_id = int(box.cls[0])
                label = self.model.names[class_id]

                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": conf,
                    "class_id": class_id,
                    "label": label
                })

        return detections

    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes on frame
        """
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = f"{det['label']} {det['confidence']:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return frame
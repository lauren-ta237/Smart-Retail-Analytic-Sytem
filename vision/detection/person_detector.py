from ultralytics import YOLO

from ultralytics import YOLO

class PersonDetector:
    # detects person in the frame using yolo
    def __init__(self):
        # load pretrained YOLO model
        self.model = YOLO('yolov8n.pt')

    def detect(self, frame):
        # detects people and return bounding boxes
        results = self.model(frame)
        persons = []
        for r in results:
            for box in r.boxes:
                class_id = int(box.cls)
                # class 0 represents 'person'
                if class_id == 0:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    persons.append((x1, y1, x2, y2))
        return persons
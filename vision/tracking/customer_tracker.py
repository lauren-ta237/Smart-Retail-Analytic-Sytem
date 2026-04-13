import os
from pathlib import Path

from dotenv import load_dotenv
from ultralytics import YOLO

try:
    import torch
except Exception:  # pragma: no cover - torch is expected but keep fallback safe
    torch = None


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class CustomerTracker:
    def __init__(
        self,
        model_path=None,
        conf=None,
        imgsz=None,
        iou=None,
        max_det=None,
        person_only=None,
        vid_stride=None,
    ):
        """
        ByteTrack-based tracker using Ultralytics YOLO.
        Tuned to reduce NMS load during customer tracking.
        """

        configured_model = model_path or os.getenv("PERSON_MODEL", "yolov8n.pt")
        configured_path = Path(configured_model)

        if not configured_path.exists():
            fallback_path = Path(__file__).resolve().parents[2] / "yolov8n.pt"
            configured_model = str(fallback_path if fallback_path.exists() else configured_model)

        self.device = os.getenv("DEVICE", "cpu")
        if self.device.startswith("cuda") and (torch is None or not torch.cuda.is_available()):
            self.device = "cpu"

        self.half = (
            os.getenv("YOLO_HALF", "true").lower() in {"1", "true", "yes", "on"}
            and self.device.startswith("cuda")
        )
        self.conf = float(conf if conf is not None else os.getenv("TRACK_CONFIDENCE", "0.45"))
        self.imgsz = int(imgsz if imgsz is not None else os.getenv("YOLO_IMGSZ", "640"))
        self.iou = float(iou if iou is not None else os.getenv("YOLO_IOU", "0.45"))
        self.max_det = int(max_det if max_det is not None else os.getenv("YOLO_MAX_DET", "40"))
        person_only_value = person_only if person_only is not None else os.getenv("YOLO_PERSON_ONLY", "true")
        self.classes = [0] if str(person_only_value).lower() in {"1", "true", "yes", "on"} else None
        self.vid_stride = int(vid_stride if vid_stride is not None else os.getenv("YOLO_VID_STRIDE", "1"))

        self.model = YOLO(configured_model)

    def update(self, frame):
        """
        Runs detection + tracking in one step.

        Returns:
            list of:
            {
                "id": int,
                "bbox": [x1, y1, x2, y2]
            }
        """

        results = self.model.track(
            frame,
            persist=True,
            conf=self.conf,
            iou=self.iou,
            imgsz=self.imgsz,
            max_det=self.max_det,
            classes=self.classes,
            vid_stride=self.vid_stride,
            device=self.device,
            half=self.half,
            tracker="bytetrack.yaml",
            verbose=False
        )

        output = []

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                if box.id is None:
                    continue

                x1, y1, x2, y2 = box.xyxy[0]
                track_id = int(box.id[0])

                output.append({
                    "id": track_id,
                    "bbox": [
                        int(x1),
                        int(y1),
                        int(x2),
                        int(y2)
                    ]
                })

        return output
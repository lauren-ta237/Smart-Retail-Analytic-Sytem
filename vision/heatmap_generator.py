import numpy as np
import cv2

# this shows hot areas, and cold areas in the shop
class HeatmapGenerator:
    def __init__(self, decay=0.95, blur_kernel=15):
        self.heatmap = None
        self.decay = decay
        self.blur_kernel = blur_kernel

    def update(self, frame, tracked_objects):
        """
        frame: np.ndarray (camera frame)
        tracked_objects: list of dicts with bbox
        """

        if frame is None:
            return

        if self.heatmap is None:
            h, w = frame.shape[:2]
            self.heatmap = np.zeros((h, w), dtype=np.float32)

        # decay old heat
        self.heatmap *= self.decay

        # accumulate positions
        for obj in tracked_objects:
            try:
                x1, y1, x2, y2 = obj["bbox"]

                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                h, w = self.heatmap.shape

                if 0 <= cx < w and 0 <= cy < h:
                    self.heatmap[cy, cx] += 1

            except Exception:
                continue

    def render(self, frame):
        if self.heatmap is None:
            return frame

        heatmap = cv2.GaussianBlur(
            self.heatmap,
            (self.blur_kernel, self.blur_kernel),
            0
        )

        heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX)
        heatmap = heatmap.astype(np.uint8)

        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

        return cv2.addWeighted(frame, 0.7, heatmap, 0.3, 0)
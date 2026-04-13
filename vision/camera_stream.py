import cv2 

class CameraStream:
    """ 
    Handles connection to a camera or video stream .
    WORKS WITH:
    - local webcam
    - CCTV camera
    - RTSP IP camera used in stores
    """

    def __init__(self, source=0):
        """
        source:
        0 = laptop/webcam
        "rtsp://..." = IP camera
        """
        self.source = source
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise Exception ('could not connect to camera')
        
    def get_frame(self):
        # reads a frame from the camera stream
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame
    
    def release(self):
        # release camera resources
        self.cap.release()
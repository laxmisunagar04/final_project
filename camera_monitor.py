import cv2


class CameraMonitor:

    def __init__(self):

        self.camera = None

    def start(self):

        self.camera = cv2.VideoCapture(0)

        if not self.camera.isOpened():
            return False

        return True

    def read_frame(self):

        if self.camera is None:
            return None

        success, frame = self.camera.read()

        if not success:
            return None

        return frame

    def stop(self):

        if self.camera is not None:
            self.camera.release()
            self.camera = None
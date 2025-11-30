import cv2
import threading

class BufferlessVideoCapture:
    def __init__(self, name):
        self.cap = cv2.VideoCapture(name)
        self.lock = threading.Lock()
        self.closed = False
        self.t = threading.Thread(target=self._reader)
        self.t.daemon = True
        self.t.start()
        print(f"Opened camera {name} {type(name)}")
    # grab frames as soon as they are available
    def _reader(self):
        while True:
            with self.lock:
                ret = self.cap.grab()
            if not ret:
                break

    # retrieve latest frame
    def read(self):
        with self.lock:
            _, frame = self.cap.retrieve()
        return frame

    def close(self):
        with self.lock:
            self.closed = True
            self.cap.release()


import threading

class LiveRequestTracker:
    _instance_lock = threading.Lock()
    liveRequestCount = 0

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            with cls._instance_lock:
                if not hasattr(cls, '_instance'):
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    def increment(self):
        with threading.Lock():
            self.liveRequestCount += 1

    def decrement(self):
        with threading.Lock():
            self.liveRequestCount -= 1

    def get(self):
        with threading.Lock():
            return self.liveRequestCount

    def reset(self):
        with threading.Lock():
            self.liveRequestCount = 0
        
        
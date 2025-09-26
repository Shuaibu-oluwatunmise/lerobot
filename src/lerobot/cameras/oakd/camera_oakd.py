import logging
import time
from threading import Event, Lock, Thread

import depthai as dai
import numpy as np

from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from ..camera import Camera
from .configuration_oakd import OakDCameraConfig

logger = logging.getLogger(__name__)


class OakDCamera(Camera):
    """OAK-D camera using depthai library."""
    
    def __init__(self, config: OakDCameraConfig):
        super().__init__(config)
        self.config = config
        
        self.pipeline = None
        self.device = None
        self.queue = None
        
        # Async reading support
        self.thread: Thread | None = None
        self.stop_event: Event | None = None
        self.frame_lock: Lock = Lock()
        self.latest_frame: np.ndarray | None = None
        self.new_frame_event: Event = Event()
    
    def __str__(self) -> str:
        return f"OakDCamera({self.config.socket})"
    
    @staticmethod
    def find_cameras():
        """Find available OAK-D cameras."""
        import depthai as dai
        
        found_cameras = []
        try:
            devices = dai.Device.getAllAvailableDevices()
            for i, device_info in enumerate(devices):
                found_cameras.append({
                    "name": f"OAK-D @ {device_info.getMxId()}",
                    "type": "oakd",
                    "id": device_info.getMxId(),
                    "usb_speed": device_info.state.name,
                })
        except Exception as e:
            logger.warning(f"Error finding OAK-D cameras: {e}")
        
        return found_cameras
    
    @property
    def is_connected(self) -> bool:
        return self.device is not None
    
    def connect(self, warmup: bool = True):
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")
        
        # Create pipeline
        self.pipeline = dai.Pipeline()
        
        # Color camera
        cam = self.pipeline.createColorCamera()
        cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        cam.setPreviewSize(self.config.width, self.config.height)
        cam.setInterleaved(True)  # BGR format
        cam.setFps(self.config.fps)
        cam.setBoardSocket(getattr(dai.CameraBoardSocket, self.config.socket))
        
        # Output
        xout = self.pipeline.createXLinkOut()
        xout.setStreamName("preview")
        cam.preview.link(xout.input)
        
        # Connect
        self.device = dai.Device(self.pipeline)
        self.queue = self.device.getOutputQueue(name="preview", maxSize=4, blocking=False)
        
        # Warmup with sync reads first
        if warmup:
            for _ in range(5):
                self.read()
                time.sleep(0.1)
        
        # Now start async thread and warm it up
        self._start_read_thread()
        time.sleep(1.0)  # Give thread time to start
        
        logger.info(f"{self} connected at {self.config.width}x{self.config.height}@{self.config.fps}fps")
    def read(self) -> np.ndarray:
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} not connected")
        
        frame_data = self.queue.get()
        frame = frame_data.getCvFrame()
        
        # Convert BGR to RGB (LeRobot expects RGB)
        import cv2
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        return frame
    
    def _read_loop(self):
        """Background thread for async reading."""
        while not self.stop_event.is_set():
            try:
                frame = self.read()
                with self.frame_lock:
                    self.latest_frame = frame
                self.new_frame_event.set()
            except DeviceNotConnectedError:
                break
            except Exception as e:
                logger.warning(f"Error in read loop: {e}")
    
    def _start_read_thread(self):
        if self.thread is not None and self.thread.is_alive():
            return
        
        self.stop_event = Event()
        self.thread = Thread(target=self._read_loop, daemon=True)
        self.thread.start()
    
    def _stop_read_thread(self):
        if self.stop_event:
            self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
    
    def async_read(self, timeout_ms: float = 200) -> np.ndarray:
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} not connected")
        
        if self.thread is None or not self.thread.is_alive():
            self._start_read_thread()
        
        if not self.new_frame_event.wait(timeout=timeout_ms / 1000.0):
            raise TimeoutError(f"Timeout waiting for frame from {self}")
        
        with self.frame_lock:
            frame = self.latest_frame
            self.new_frame_event.clear()
        
        return frame
    
    def disconnect(self):
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} not connected")
        
        self._stop_read_thread()
        
        if self.device:
            self.device.close()
            self.device = None
            self.queue = None
            self.pipeline = None
        
        logger.info(f"{self} disconnected")

    
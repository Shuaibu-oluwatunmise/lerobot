import depthai as dai
import numpy as np
import cv2

pipeline = dai.Pipeline()

# Color camera
cam = pipeline.createColorCamera()
cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
cam.setPreviewSize(640, 480)
cam.setInterleaved(True)  # This is key - makes it BGR format OpenCV likes
cam.setBoardSocket(dai.CameraBoardSocket.CAM_A)  # Explicitly use IMX214

# Output
xout = pipeline.createXLinkOut()
xout.setStreamName("preview")
cam.preview.link(xout.input)

print("Starting device...")
with dai.Device(pipeline) as device:
    print("Device started successfully")
    q = device.getOutputQueue(name="preview", maxSize=4, blocking=False)
    
    print("Getting frames... Press 'q' to quit")
    while True:
        frame_data = q.get()
        frame = frame_data.getCvFrame()
        
        print(f"Frame shape: {frame.shape}, dtype: {frame.dtype}")
        cv2.imshow("OAK-D", frame)
        
        if cv2.waitKey(1) == ord('q'):
            break
    
    cv2.destroyAllWindows()
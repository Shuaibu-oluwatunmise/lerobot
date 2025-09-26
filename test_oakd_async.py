from lerobot.cameras.oakd import OakDCamera, OakDCameraConfig

config = OakDCameraConfig(fps=30, width=640, height=480)
camera = OakDCamera(config)

print("Connecting camera...")
camera.connect()

print("Testing async read...")
for i in range(10):
    frame = camera.async_read(timeout_ms=1000)
    print(f"Frame {i}: {frame.shape}")

camera.disconnect()
print("Done")
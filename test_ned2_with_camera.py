from lerobot.robots.utils import make_robot_from_config
from lerobot.robots.ned2_follower import Ned2FollowerConfig

# Create config with OAK-D camera
config = Ned2FollowerConfig(
    id="my_ned2",
    ip_address="192.168.8.143"
)

print(f"Config: {config}")
print(f"Cameras configured: {list(config.cameras.keys())}")

# Create robot
robot = make_robot_from_config(config)
print(f"\nRobot created: {robot}")
print(f"Observation features: {robot.observation_features}")

# Connect
print("\nConnecting to robot and camera...")
robot.connect(calibrate=False)
print("Connected!")

# Get observation (joints + camera image)
print("\nGetting observation...")
obs = robot.get_observation()

print(f"\nObservation keys: {list(obs.keys())}")
print(f"Joint positions: {[obs[f'joint_{i}.pos'] for i in range(1, 7)]}")
print(f"Camera image shape: {obs['top'].shape}")

# Disconnect
print("\nDisconnecting...")
robot.disconnect()
print("Done!")
from lerobot.robots.utils import make_robot_from_config
from lerobot.robots.ned2_follower import Ned2FollowerConfig

# Create config
config = Ned2FollowerConfig(
    id="my_ned2",
    ip_address="192.168.8.143"
)

print(f"Config created: {config}")
print(f"Robot type: {config.type}")

# Try to create robot (don't connect yet)
robot = make_robot_from_config(config)
print(f"Robot created: {robot}")
print(f"Observation features: {robot.observation_features}")
print(f"Action features: {robot.action_features}")

print("\nSuccess! Ned2 is integrated with LeRobot!")
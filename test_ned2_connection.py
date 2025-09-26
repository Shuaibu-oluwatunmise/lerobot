from lerobot.robots.utils import make_robot_from_config
from lerobot.robots.ned2_follower import Ned2FollowerConfig

# Create config
config = Ned2FollowerConfig(
    id="my_ned2",
    ip_address="192.168.8.143"
)

# Create robot
robot = make_robot_from_config(config)
print(f"Robot created: {robot}")

# Connect to robot
print("\nConnecting to Ned2...")
robot.connect(calibrate=False)
print("Connected!")

# Read observation
print("\nReading observation...")
obs = robot.get_observation()
print(f"Joint positions: {obs}")

# Send a small movement
print("\nSending small movement command...")
action = {
    "joint_1.pos": obs["joint_1.pos"] + 0.05,
    "joint_2.pos": obs["joint_2.pos"],
    "joint_3.pos": obs["joint_3.pos"],
    "joint_4.pos": obs["joint_4.pos"],
    "joint_5.pos": obs["joint_5.pos"],
    "joint_6.pos": obs["joint_6.pos"],
}
robot.send_action(action)
print("Movement sent!")

# Disconnect
print("\nDisconnecting...")
robot.disconnect()
print("Done!")
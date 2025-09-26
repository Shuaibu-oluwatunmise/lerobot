from pyniryo import NiryoRobot

robot = NiryoRobot("192.168.8.143")

# Check if there's a method to get joint limits
print("Looking for joint limit info...")
try:
    # Try common methods
    print(f"\nPose info: {robot.get_pose()}")
except Exception as e:
    print(f"get_pose error: {e}")

# Check documentation attribute if exists
if hasattr(robot, '__doc__'):
    print(f"\nDocumentation available")

robot.close_connection()
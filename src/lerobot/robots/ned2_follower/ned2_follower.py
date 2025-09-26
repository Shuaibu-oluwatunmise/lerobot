#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import time
from functools import cached_property
from typing import Any

from pyniryo import NiryoRobot

from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from ..robot import Robot
from ..utils import ensure_safe_goal_position
from .config_ned2_follower import Ned2FollowerConfig

logger = logging.getLogger(__name__)


class Ned2Follower(Robot):
    """
    Ned2 robot from Niryo integrated with LeRobot.
    """

    config_class = Ned2FollowerConfig
    name = "ned2_follower"

    def __init__(self, config: Ned2FollowerConfig):
        super().__init__(config)
        self.config = config
        self.robot = None
        self.cameras = make_cameras_from_configs(config.cameras)

    @property
    def _motors_ft(self) -> dict[str, type]:
        """Define motor observation features (joint positions)."""
        return {
            "joint_1.pos": float,
            "joint_2.pos": float,
            "joint_3.pos": float,
            "joint_4.pos": float,
            "joint_5.pos": float,
            "joint_6.pos": float,
        }

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        """Define camera observation features."""
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) 
            for cam in self.cameras
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        return self._motors_ft

    @property
    def is_connected(self) -> bool:
        return (
            self.robot is not None 
            and all(cam.is_connected for cam in self.cameras.values())
        )

    def connect(self, calibrate: bool = True) -> None:
        """Connect to the Ned2 robot."""
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        logger.info(f"Connecting to Ned2 at {self.config.ip_address}:{self.config.port}")
        self.robot = NiryoRobot(self.config.ip_address)
        
        if calibrate and self.config.calibrate_on_connect:
            if self.robot.need_calibration():
                logger.info("Calibrating Ned2...")
                self.robot.calibrate_auto()

        for cam in self.cameras.values():
            cam.connect()

        self.configure()
        logger.info(f"{self} connected.")

    @property
    def is_calibrated(self) -> bool:
        """Ned2 handles calibration internally."""
        if self.robot is None:
            return True
        return not self.robot.need_calibration()

    def calibrate(self) -> None:
        """Calibrate the Ned2 robot."""
        if self.robot is None:
            raise DeviceNotConnectedError(f"{self} is not connected.")
        
        logger.info("Running Ned2 calibration...")
        self.robot.calibrate_auto()
        logger.info("Calibration complete.")

    def configure(self) -> None:
        """Configure robot settings."""
        if self.robot is None:
            raise DeviceNotConnectedError(f"{self} is not connected.")
        
        # Enable learning mode for safety during setup
        self.robot.set_learning_mode(True)
        time.sleep(0.1)
        self.robot.set_learning_mode(False)
        
        logger.info(f"{self} configured.")

    def get_observation(self) -> dict[str, Any]:
        """Read current robot state."""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        # Small delay to avoid overwhelming Ned2 communication
        time.sleep(0.01)  # 10ms delay

        # Read joint positions
        start = time.perf_counter()
        joints = self.robot.joints
        joints_list = list(joints)
        
        obs_dict = {
            "joint_1.pos": float(joints_list[0]), 
            "joint_2.pos": float(joints_list[1]),
            "joint_3.pos": float(joints_list[2]),
            "joint_4.pos": float(joints_list[3]),
            "joint_5.pos": float(joints_list[4]),
            "joint_6.pos": float(joints_list[5]),
        }
        
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read state: {dt_ms:.1f}ms")

        # Capture images from cameras
        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.read()
            dt_ms = (time.perf_counter() - start) * 1e3
            logger.debug(f"{self} read {cam_key}: {dt_ms:.1f}ms")

        return obs_dict

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Send action commands to the robot."""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        # Extract goal positions
        goal_pos = {
            key.removesuffix(".pos"): val 
            for key, val in action.items() 
            if key.endswith(".pos")
        }

        # Apply safety limits if configured
        if self.config.max_relative_target is not None:
            present_joints = list(self.robot.joints)
            present_pos = {
                f"joint_{i+1}": present_joints[i] 
                for i in range(6)
            }
            goal_present_pos = {
                key: (g_pos, present_pos[key]) 
                for key, g_pos in goal_pos.items()
            }
            goal_pos = ensure_safe_goal_position(
                goal_present_pos, 
                self.config.max_relative_target
            )

        # Convert to individual joint values and send
        j1 = goal_pos.get("joint_1", 0)
        j2 = goal_pos.get("joint_2", 0)
        j3 = goal_pos.get("joint_3", 0)
        j4 = goal_pos.get("joint_4", 0)
        j5 = goal_pos.get("joint_5", 0)
        j6 = goal_pos.get("joint_6", 0)
        
        # Use move_joints (deprecated but works) or try move with unpacked args
        self.robot.move_joints(j1, j2, j3, j4, j5, j6)
        
        return {f"{motor}.pos": val for motor, val in goal_pos.items()}

    def disconnect(self):
        """Disconnect from the robot."""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        if self.robot:
            self.robot.close_connection()
            self.robot = None

        for cam in self.cameras.values():
            cam.disconnect()

        logger.info(f"{self} disconnected.")
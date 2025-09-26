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

from dataclasses import dataclass, field

from lerobot.cameras.oakd import OakDCameraConfig

from ..config import RobotConfig


@RobotConfig.register_subclass("ned2_follower")
@dataclass
class Ned2FollowerConfig(RobotConfig):
    """Configuration for Ned2 robot from Niryo."""
    
    # Connection settings
    ip_address: str = "192.168.8.143"
    port: int = 40001
    
    # Joint limits (radians)
    joint_limits: dict = field(default_factory=lambda: {
        "joint_1": (-2.949, 2.949),
        "joint_2": (-1.83, 0.61),
        "joint_3": (-1.34, 1.57),
        "joint_4": (-2.089, 2.089),
        "joint_5": (-1.919, 1.922),
        "joint_6": (-2.53, 2.53),
    })
    
    # Safety limits
    max_relative_target: float | dict[str, float] | None = None
    
    # Camera configuration
    cameras: dict[str, OakDCameraConfig] = field(default_factory=lambda: {
        "top": OakDCameraConfig(
            fps=30,
            width=640,
            height=480,
            socket="CAM_A"
        )
    })
    
    # Other settings
    has_gripper: bool = True
    disable_torque_on_disconnect: bool = False
    calibrate_on_connect: bool = False
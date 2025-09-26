from dataclasses import dataclass

from ..configs import CameraConfig


@CameraConfig.register_subclass("oakd")
@dataclass
class OakDCameraConfig(CameraConfig):
    """Configuration for OAK-D camera using depthai."""
    
    # Inherited from CameraConfig:
    # fps: int | None
    # width: int | None  
    # height: int | None
    
    # OAK-D specific
    socket: str = "CAM_A"  # Which camera socket to use
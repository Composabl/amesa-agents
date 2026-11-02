from typing import Dict, List

import numpy as np

from amesa_core import PerceptorImpl


def _scalar(value) -> float:
    """Sensors arrive as numpy arrays (a scalar sensor has shape (1,)); unwrap to a float."""
    return float(np.asarray(value, dtype=np.float64).reshape(-1)[0])


class KinematicsPerceptor(PerceptorImpl):
    """
    Derives velocity and acceleration from consecutive position readings.

    Reads:
        position (float): Position sensor (metres).
        dt       (float): Elapsed time since the last step (seconds).
                          If the orchestration has no dt sensor, a fixed
                          timestep of 0.05 s is assumed.

    Produces:
        velocity     (float): First derivative of position (m/s).
        acceleration (float): Second derivative of position (m/s²).

    Both outputs are 0.0 on the first step of each episode because no
    prior position is available. The runtime creates a fresh instance
    (calls __init__ again) at every episode reset, so state never leaks
    across episodes.
    """

    DEFAULT_DT = 0.05  # seconds, used when there is no dt sensor

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.prev_position: float | None = None
        self.prev_velocity: float | None = None

    async def compute(self, obs_spec, obs) -> Dict[str, float]:
        position = _scalar(obs["position"])
        dt = _scalar(obs["dt"]) if "dt" in obs else self.DEFAULT_DT

        if self.prev_position is None:
            velocity = 0.0
            acceleration = 0.0
        else:
            velocity = (position - self.prev_position) / dt if dt > 0.0 else 0.0
            if self.prev_velocity is None:
                acceleration = 0.0
            else:
                acceleration = (velocity - self.prev_velocity) / dt if dt > 0.0 else 0.0

        self.prev_position = position
        self.prev_velocity = velocity

        return {
            "velocity": velocity,
            "acceleration": acceleration,
        }

    def filtered_sensor_space(self, obs) -> List[str]:
        return ["position", "dt"]
